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

# Dynamic interval constants
BASE_INTERVAL = 15        # Default interval for stable courses
FAST_INTERVAL = 5         # Fast interval for recently changed courses
SLOW_INTERVAL = 20        # Slow interval for consistently closed courses
OPEN_COURSE_INTERVAL = 30 # Check open courses every 30 seconds (to track seat changes)
RECENTLY_CHANGED_THRESHOLD = 5  # Consider course "recently changed" if status changed in last 5 checks

# Georgia Tech OSCAR endpoint
ENDPOINT = 'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in=%s&crn_in=%s'

# Regex patterns for parsing (updated to match actual HTML structure)
_NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)
# Updated to handle SPAN tags and parse the seats row: Capacity, Actual, Remaining
_SEATS_ROW_RE = re.compile(r'<SPAN[^>]*>Seats</SPAN></th>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(\d+)</td>', re.IGNORECASE | re.DOTALL)

def handler(event, context):
    """Handle the Lambda event to scrape course availability with dynamic intervals.
    
    Args:
        event (dict): The Lambda event.
        context (object): The Lambda context.
        
    Returns:
        dict: Response with status code and body.
    """
    start_time = time.time()
    logger.info('Starting scraper with dynamic intervals')
    
    while (time.time() - start_time) < MAX_RUNTIME:
        try:
            loop_start = time.time()
            
            # Get CRNs to check from DynamoDB with their metadata
            db_start = time.time()
            crns_to_check, current_statuses, crn_metadata = get_crns_to_check_with_metadata()
            db_time = time.time() - db_start
            logger.info(f'DynamoDB scan took {db_time:.2f}s for {len(crns_to_check)} CRNs to check')
            
            if not crns_to_check:
                logger.info('No CRNs found to process')
                next_interval = BASE_INTERVAL
            else:
                logger.info(f'Processing {len(crns_to_check)} CRNs')
                scrape_start = time.time()
                asyncio.run(process_crns_with_metadata(crns_to_check, current_statuses, crn_metadata))
                scrape_time = time.time() - scrape_start
                logger.info(f'Scraping took {scrape_time:.2f}s for {len(crns_to_check)} CRNs')
                
                # Calculate next interval based on what happened
                next_interval = calculate_next_interval(crn_metadata)
            
            loop_time = time.time() - loop_start
            logger.info(f'Total loop time: {loop_time:.2f}s')
            
            # Check if we have time for another loop
            remaining_time = MAX_RUNTIME - (time.time() - start_time)
            if remaining_time < next_interval:
                logger.info(f'Not enough time for another check (need {next_interval}s, have {remaining_time:.2f}s)')
                break
                
            logger.info(f'Sleeping for {next_interval}s (dynamic interval)')
            time.sleep(next_interval)
            
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
    """Get all CRNs that need to be checked from DynamoDB using normalized structure.
    
    Returns:
        Tuple[Set[str], Dict[str, str]]: Set of CRNs to check and their current statuses.
    """
    try:
        # Get all CRNs directly from the CRNs table (much more efficient)
        crns_table = dynamodb.Table(os.environ.get('DYNAMODB_CRNS_TABLE', 'reaper-crns'))
        response = crns_table.scan()
        
        crns_to_check = set()
        current_statuses = {}
        
        for crn_item in response.get('Items', []):
            crn = crn_item.get('crn')
            if crn and crn_item.get('users'):  # Only check CRNs that have users tracking them
                crns_to_check.add(crn)
                # Track current status (default to closed if not set)
                current_statuses[crn] = 'open' if crn_item.get('isOpen', False) else 'closed'
        
        logger.info(f"Found {len(crns_to_check)} unique CRNs to check")
        return crns_to_check, current_statuses
        
    except Exception as e:
        logger.error(f"Error getting CRNs from DynamoDB: {str(e)}")
        return set(), {}

def get_crns_to_check_with_metadata() -> Tuple[Set[str], Dict[str, str], Dict[str, Dict]]:
    """Get all CRNs with metadata for dynamic interval calculation.
    
    Returns:
        Tuple[Set[str], Dict[str, str], Dict[str, Dict]]: CRNs to check, current statuses, and metadata.
    """
    try:
        crns_table = dynamodb.Table(os.environ.get('DYNAMODB_CRNS_TABLE', 'reaper-crns'))
        response = crns_table.scan()
        
        crns_to_check = set()
        current_statuses = {}
        crn_metadata = {}
        
        for crn_item in response.get('Items', []):
            crn = crn_item.get('crn')
            if crn and crn_item.get('users'):  # Only check CRNs that have users tracking them
                crns_to_check.add(crn)
                current_statuses[crn] = 'open' if crn_item.get('isOpen', False) else 'closed'
                
                # Store metadata for dynamic interval calculation
                crn_metadata[crn] = {
                    'last_updated': crn_item.get('last_updated'),
                    'isOpen': crn_item.get('isOpen', False),
                    'seats_remaining': crn_item.get('seats_remaining', 0),
                    'total_seats': crn_item.get('total_seats', 0),
                    'users_count': len(crn_item.get('users', [])),
                    'last_status_change': crn_item.get('last_status_change'),  # We'll add this
                    'consecutive_closed_checks': crn_item.get('consecutive_closed_checks', 0)  # We'll add this
                }
        
        logger.info(f"Found {len(crns_to_check)} unique CRNs to check with metadata")
        return crns_to_check, current_statuses, crn_metadata
        
    except Exception as e:
        logger.error(f"Error getting CRNs with metadata from DynamoDB: {str(e)}")
        return set(), {}, {}

def calculate_next_interval(crn_metadata: Dict[str, Dict]) -> int:
    """Calculate the next check interval based on CRN metadata with improved logic.
    
    Args:
        crn_metadata (Dict[str, Dict]): Metadata for all CRNs.
        
    Returns:
        int: Next interval in seconds.
    """
    if not crn_metadata:
        return BASE_INTERVAL
    
    # Count different types of courses
    recently_opened = 0      # Just opened (status changed in last few checks)
    stable_open = 0          # Been open for a while
    high_demand_closed = 0   # Closed but high demand (3+ users)
    consistently_closed = 0  # Closed for many checks
    recently_changed = 0     # Any recent status change
    
    for crn, metadata in crn_metadata.items():
        users_count = metadata.get('users_count', 0)
        consecutive_closed = metadata.get('consecutive_closed_checks', 0)
        is_open = metadata.get('isOpen', False)
        last_status_change = metadata.get('last_status_change')
        
        # Check if recently changed (within threshold)
        is_recently_changed = consecutive_closed <= RECENTLY_CHANGED_THRESHOLD
        
        if is_open:
            if is_recently_changed:
                recently_opened += 1
            else:
                stable_open += 1
        else:  # Course is closed
            if users_count >= 3:  # High demand course
                high_demand_closed += 1
            elif consecutive_closed >= 15:  # Consistently closed for many checks
                consistently_closed += 1
            elif is_recently_changed:
                recently_changed += 1
    
    # Determine interval based on course mix (prioritized logic)
    if recently_opened > 0 or recently_changed > 0:
        # Fast interval for recently changed courses (need quick detection)
        interval = FAST_INTERVAL
        logger.info(f"Using FAST interval ({FAST_INTERVAL}s) - {recently_opened} recently opened, {recently_changed} recently changed")
    
    elif stable_open > 0:
        # Open courses get checked every 30s to track seat changes
        interval = OPEN_COURSE_INTERVAL
        logger.info(f"Using OPEN interval ({OPEN_COURSE_INTERVAL}s) - {stable_open} stable open courses")
    
    elif high_demand_closed > consistently_closed:
        # Base interval for high-demand closed courses
        interval = BASE_INTERVAL
        logger.info(f"Using BASE interval ({BASE_INTERVAL}s) - {high_demand_closed} high demand, {consistently_closed} consistently closed")
    
    else:
        # Slow interval for mostly consistently closed courses
        interval = SLOW_INTERVAL
        logger.info(f"Using SLOW interval ({SLOW_INTERVAL}s) - mostly consistently closed courses")
    
    return interval

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

async def process_crns_with_metadata(crns_list: Set[str], current_statuses: Dict[str, str], crn_metadata: Dict[str, Dict]) -> None:
    """Process multiple CRNs concurrently with metadata tracking.
    
    Args:
        crns_list (Set[str]): Set of CRNs to process.
        current_statuses (Dict[str, str]): Current status of each CRN.
        crn_metadata (Dict[str, Dict]): Metadata for each CRN.
    """
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=50)) as session:
        tasks = [check_course_open(session, crn) for crn in crns_list]
        results = await asyncio.gather(*tasks)
        
        for crn, availability_data in results:
            try:
                if availability_data is None:
                    logger.warning(f"Could not check availability for CRN {crn}")
                    # Increment consecutive closed checks for failed requests
                    update_crn_metadata(crn, crn_metadata.get(crn, {}), None, current_statuses.get(crn, 'closed'))
                    continue
                
                is_open = availability_data.get('is_open', False)
                was_closed = current_statuses.get(crn, 'closed') == 'closed'
                
                # Update CRN data with metadata tracking
                update_crn_data_with_metadata(crn, availability_data, crn_metadata.get(crn, {}), current_statuses.get(crn, 'closed'))
                
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
    """Update CRN data in the normalized CRNs table.
    
    Args:
        crn (str): The CRN to update.
        availability (Dict): The availability data.
    """
    try:
        crns_table = dynamodb.Table(os.environ.get('DYNAMODB_CRNS_TABLE', 'reaper-crns'))
        
        # Get existing CRN record to preserve users list
        response = crns_table.get_item(Key={'crn': crn})
        if 'Item' not in response:
            logger.warning(f"CRN {crn} not found in CRNs table")
            return
        
        existing_crn = response['Item']
        existing_users = existing_crn.get('users', [])
        
        # Update the CRN record with new availability data
        updated_crn = {
            'crn': crn,
            'course_name': availability.get('course_name', existing_crn.get('course_name')),
            'course_id': availability.get('course_id', existing_crn.get('course_id')),
            'course_section': availability.get('course_section', existing_crn.get('course_section')),
            'isOpen': availability.get('is_open', False),
            'seats_remaining': availability.get('seats_remaining', 0),
            'total_seats': availability.get('total_seats', 0),
            'users': existing_users,  # Preserve the users list
            'last_updated': availability.get('last_checked')
        }
        
        crns_table.put_item(Item=updated_crn)
        logger.info(f"Updated CRN {crn} data for {len(existing_users)} users")
        
    except Exception as e:
        logger.error(f"Error updating CRN data for {crn}: {str(e)}")

def update_crn_data_with_metadata(crn: str, availability: Dict, old_metadata: Dict, old_status: str) -> None:
    """Update CRN data with metadata tracking for dynamic intervals.
    
    Args:
        crn (str): The CRN to update.
        availability (Dict): The availability data.
        old_metadata (Dict): Previous metadata.
        old_status (str): Previous status.
    """
    try:
        crns_table = dynamodb.Table(os.environ.get('DYNAMODB_CRNS_TABLE', 'reaper-crns'))
        
        # Get existing CRN record to preserve users list
        response = crns_table.get_item(Key={'crn': crn})
        if 'Item' not in response:
            logger.warning(f"CRN {crn} not found in CRNs table")
            return
        
        existing_crn = response['Item']
        existing_users = existing_crn.get('users', [])
        
        new_is_open = availability.get('is_open', False)
        new_status = 'open' if new_is_open else 'closed'
        
        # Track status changes
        status_changed = old_status != new_status
        last_status_change = existing_crn.get('last_status_change')
        if status_changed:
            last_status_change = availability.get('last_checked')
        
        # Track consecutive closed checks
        consecutive_closed = existing_crn.get('consecutive_closed_checks', 0)
        if new_status == 'closed':
            consecutive_closed += 1
        else:
            consecutive_closed = 0
        
        # Update the CRN record with new availability data and metadata
        updated_crn = {
            'crn': crn,
            'course_name': availability.get('course_name', existing_crn.get('course_name')),
            'course_id': availability.get('course_id', existing_crn.get('course_id')),
            'course_section': availability.get('course_section', existing_crn.get('course_section')),
            'isOpen': new_is_open,
            'seats_remaining': availability.get('seats_remaining', 0),
            'total_seats': availability.get('total_seats', 0),
            'users': existing_users,  # Preserve the users list
            'last_updated': availability.get('last_checked'),
            'last_status_change': last_status_change,
            'consecutive_closed_checks': consecutive_closed
        }
        
        crns_table.put_item(Item=updated_crn)
        logger.info(f"Updated CRN {crn} data with metadata - consecutive_closed: {consecutive_closed}, status_changed: {status_changed}")
        
    except Exception as e:
        logger.error(f"Error updating CRN data with metadata for {crn}: {str(e)}")

def update_crn_metadata(crn: str, old_metadata: Dict, availability: Optional[Dict], old_status: str) -> None:
    """Update CRN metadata when scraping fails.
    
    Args:
        crn (str): The CRN to update.
        old_metadata (Dict): Previous metadata.
        availability (Dict): The availability data (may be None).
        old_status (str): Previous status.
    """
    try:
        crns_table = dynamodb.Table(os.environ.get('DYNAMODB_CRNS_TABLE', 'reaper-crns'))
        
        # Get existing CRN record
        response = crns_table.get_item(Key={'crn': crn})
        if 'Item' not in response:
            logger.warning(f"CRN {crn} not found in CRNs table")
            return
        
        existing_crn = response['Item']
        
        # Increment consecutive closed checks for failed requests
        consecutive_closed = existing_crn.get('consecutive_closed_checks', 0) + 1
        
        # Update only the metadata fields
        existing_crn['consecutive_closed_checks'] = consecutive_closed
        
        crns_table.put_item(Item=existing_crn)
        logger.info(f"Updated CRN {crn} metadata - consecutive_closed: {consecutive_closed} (failed request)")
        
    except Exception as e:
        logger.error(f"Error updating CRN metadata for {crn}: {str(e)}")

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