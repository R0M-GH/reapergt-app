import json
import boto3
import os
import logging
import requests
import time
import re
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Set, Tuple, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LAMBDA RUNTIME CONSTANTS
MAX_RUNTIME = 780  # 13 minutes in seconds

# AWS RESOURCE CONSTANTS
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# COURSE SCRAPING CONSTANTS
TERM = '202508'  # Spring 2025
CHECK_INTERVAL = 15  # Check every 15 seconds

# Georgia Tech OSCAR endpoint
ENDPOINT = 'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in=%s&crn_in=%s'

# Regex patterns for parsing (updated to match actual HTML structure)
_NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)
# Updated to handle SPAN tags and parse the seats row: Capacity, Actual, Remaining
_SEATS_ROW_RE = re.compile(r'<SPAN[^>]*>Seats</SPAN></th>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(\d+)</td>', re.IGNORECASE | re.DOTALL)

def handler(event, context):
    """Handle the Lambda event to scrape course availability with internal loop.
    
    Args:
        event (dict): The Lambda event.
        context (object): The Lambda context.
        
    Returns:
        dict: Response with status code and body.
    """
    start_time = time.time()
    logger.info('Starting scraper with internal loop')
    
    while (time.time() - start_time) < MAX_RUNTIME:
        try:
            loop_start = time.time()
            
            # Get CRNs to check from DynamoDB
            db_start = time.time()
            crns_to_check, current_statuses = get_crns_to_check()
            db_time = time.time() - db_start
            logger.info(f'DynamoDB scan took {db_time:.2f}s for {len(crns_to_check)} CRNs to check')
            
            if not crns_to_check:
                logger.info('No CRNs found to process')
            else:
                logger.info(f'Processing {len(crns_to_check)} CRNs')
                scrape_start = time.time()
                asyncio.run(process_crns(crns_to_check, current_statuses))
                scrape_time = time.time() - scrape_start
                logger.info(f'Scraping took {scrape_time:.2f}s for {len(crns_to_check)} CRNs')
            
            loop_time = time.time() - loop_start
            logger.info(f'Total loop time: {loop_time:.2f}s')
            
            # Check if we have time for another loop
            remaining_time = MAX_RUNTIME - (time.time() - start_time)
            if remaining_time < CHECK_INTERVAL:
                logger.info(f'Not enough time for another check (need {CHECK_INTERVAL}s, have {remaining_time:.2f}s)')
                break
                
            logger.info(f'Sleeping for {CHECK_INTERVAL}s')
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f'Error in scraper loop: {e}')
            time.sleep(5)  # Short sleep before retrying
    
    total_time = time.time() - start_time
    logger.info(f'Scraper finished after {total_time:.2f}s')
    return {
        'statusCode': 200, 
        'body': json.dumps({
            'message': 'Scraping completed successfully',
            'runtime': f'{total_time:.2f}s',
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def get_crns_to_check() -> Tuple[Set[str], Dict[str, str]]:
    """Get all CRNs that need to be checked from DynamoDB.
    
    Returns:
        Tuple[Set[str], Dict[str, str]]: Set of CRNs to check and their current statuses.
    """
    try:
        # Get all users and their CRNs
        users_table = dynamodb.Table(os.environ.get('DYNAMODB_USERS_TABLE', 'reapergt-dynamo-users'))
        response = users_table.scan()
        
        crns_to_check = set()
        current_statuses = {}
        
        for user_item in response.get('Items', []):
            crns_list = user_item.get('crns', [])
            for crn_data in crns_list:
                crn = crn_data.get('crn')
                if crn:
                    crns_to_check.add(crn)
                    # Track current status (default to closed if not set)
                    current_statuses[crn] = 'open' if crn_data.get('isOpen', False) else 'closed'
        
        logger.info(f"Found {len(crns_to_check)} unique CRNs to check")
        return crns_to_check, current_statuses
        
    except Exception as e:
        logger.error(f"Error getting CRNs from DynamoDB: {str(e)}")
        return set(), {}

async def process_crns(crns_list: Set[str], current_statuses: Dict[str, str]) -> None:
    """Process multiple CRNs concurrently.
    
    Args:
        crns_list (Set[str]): Set of CRNs to process.
        current_statuses (Dict[str, str]): Current status of each CRN.
    """
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=50)) as session:
        tasks = [check_course_open(session, crn) for crn in crns_list]
        results = await asyncio.gather(*tasks)
        
        for crn, availability_data in results:
            try:
                if availability_data is None:
                    logger.warning(f"Could not check availability for CRN {crn}")
                    continue
                
                is_open = availability_data.get('is_open', False)
                was_closed = current_statuses.get(crn, 'closed') == 'closed'
                
                # Update user data with new availability info
                update_user_crn_data(crn, availability_data)
                
                # Send notification if course just opened
                if is_open and was_closed:
                    logger.info(f'🎉 Course {crn} is now OPEN!')
                    send_notification(crn, availability_data)
                elif is_open:
                    logger.info(f'CRN {crn} remains open ({availability_data.get("seats_remaining", 0)}/{availability_data.get("total_seats", 0)} seats)')
                else:
                    logger.info(f'CRN {crn} still closed ({availability_data.get("seats_remaining", 0)}/{availability_data.get("total_seats", 0)} seats)')
                    
            except Exception as e:
                logger.error(f'Error processing results for CRN {crn}: {e}')

async def check_course_open(session: aiohttp.ClientSession, crn: str) -> Tuple[str, Optional[Dict]]:
    """Check if a course is open.
    
    Args:
        session (aiohttp.ClientSession): The HTTP session.
        crn (str): The CRN to check.
        
    Returns:
        Tuple[str, Dict]: The CRN and availability data.
    """
    url = ENDPOINT % (TERM, crn)
    try:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f'HTTP Error {response.status} fetching course data for CRN {crn}')
                return crn, None
                
            html = await response.text()
            availability_data = parse_course_data(html, crn)
            
            return crn, availability_data
            
    except Exception as e:
        logger.error(f'Error checking CRN {crn}: {e}')
        return crn, None

def parse_course_data(html: str, crn: str) -> Optional[Dict]:
    """Parse course data from HTML.
    
    Args:
        html (str): The HTML to parse.
        crn (str): The CRN being parsed.
        
    Returns:
        Dict: Course availability data.
    """
    try:
        # Check if course exists
        if _NAME_RE.search(html) is None:
            logger.warning(f"CRN {crn} does not exist or is not found")
            return None
        
        # Extract course information
        name_match = _NAME_RE.search(html)
        if name_match:
            name_parts = [part.strip().replace('<br />', '').replace('<br>', '') for part in name_match.group(1).split(" - ")]
            
            if len(name_parts) >= 4:
                course_name = name_parts[0]
                course_id = name_parts[2]
                course_section = name_parts[3]
            else:
                course_name = name_match.group(1)
                course_id = 'N/A'
                course_section = 'N/A'
        else:
            logger.warning(f"Could not extract course information for CRN {crn}")
            return None
        
        # Check seat availability
        seats_remaining = 0
        total_seats = 0
        
        seats_row_match = _SEATS_ROW_RE.search(html)
        
        if seats_row_match:
            total_seats = int(seats_row_match.group(1))  # Capacity
            actual_enrolled = int(seats_row_match.group(2))  # Actual
            seats_remaining = int(seats_row_match.group(3))  # Remaining
        else:
            logger.warning(f"Could not parse seat information for CRN {crn}")
        
        is_open = seats_remaining > 0
        
        return {
            'crn': crn,
            'course_name': course_name,
            'course_id': course_id,
            'course_section': course_section,
            'is_open': is_open,
            'seats_remaining': seats_remaining,
            'total_seats': total_seats,
            'last_checked': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error parsing course data for CRN {crn}: {str(e)}")
        return None

def update_user_crn_data(crn: str, availability: Dict) -> None:
    """Update all users' CRN data with new availability information.
    
    Args:
        crn (str): The CRN to update.
        availability (Dict): The availability data.
    """
    try:
        users_table = dynamodb.Table(os.environ.get('DYNAMODB_USERS_TABLE', 'reapergt-dynamo-users'))
        
        # Scan all users to find who has this CRN
        response = users_table.scan()
        
        for user_item in response.get('Items', []):
            user_id = user_item.get('user_id')
            crns_list = user_item.get('crns', [])
            
            # Check if this user has the CRN
            updated_crns = []
            needs_update = False
            
            for crn_data in crns_list:
                if crn_data.get('crn') == crn:
                    # Update this CRN's data
                    crn_data.update({
                        'course_name': availability.get('course_name', crn_data.get('course_name')),
                        'course_id': availability.get('course_id', crn_data.get('course_id')),
                        'course_section': availability.get('course_section', crn_data.get('course_section')),
                        'isOpen': availability.get('is_open', False),
                        'seats_remaining': availability.get('seats_remaining', 0),
                        'total_seats': availability.get('total_seats', 0),
                        'last_checked': availability.get('last_checked')
                    })
                    needs_update = True
                
                updated_crns.append(crn_data)
            
            # Update user if needed
            if needs_update:
                # Preserve ALL existing user data
                updated_user_item = user_item.copy()
                updated_user_item['user_id'] = user_id
                updated_user_item['crns'] = updated_crns
                users_table.put_item(Item=updated_user_item)
                logger.info(f"Updated user {user_id} CRN data for {crn}")
        
    except Exception as e:
        logger.error(f"Error updating user CRN data for {crn}: {str(e)}")

def send_notification(crn: str, availability: Dict) -> None:
    """Send notification about course availability by invoking notifier Lambda.
    
    Args:
        crn (str): The CRN that opened.
        availability (Dict): The availability data.
    """
    notifier_function_name = os.environ.get('NOTIFIER_FUNCTION_NAME')
    if not notifier_function_name:
        logger.error("NOTIFIER_FUNCTION_NAME environment variable not set")
        return
    
    # Create notification payload
    payload = {
        'notification_type': 'course_available',
        'crn': crn,
        'availability': availability,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Invoke notifier Lambda directly with retry logic
    lambda_client = boto3.client('lambda')
    
    for attempt in range(3):
        try:
            response = lambda_client.invoke(
                FunctionName=notifier_function_name,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            
            if response['StatusCode'] == 202:  # Success for async invocation
                logger.info(f"Notifier Lambda invoked successfully for CRN {crn} (attempt {attempt + 1})")
                return
            else:
                logger.warning(f"Unexpected status code {response['StatusCode']} for CRN {crn} (attempt {attempt + 1})")
                
        except Exception as e:
            logger.error(f"Error invoking notifier for CRN {crn} (attempt {attempt + 1}): {str(e)}")
            
            if attempt == 2:  # Last attempt
                logger.error(f"Failed to invoke notifier for CRN {crn} after 3 attempts")
                return
            
            # Wait before retrying (exponential backoff)
            time.sleep(2 ** attempt)  # 1s, 2s, 4s 