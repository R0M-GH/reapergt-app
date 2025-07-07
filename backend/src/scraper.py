import boto3
import json
import re
import aiohttp
import asyncio
import time
from typing import Union, List, Tuple, Dict, Set

def get_secrets():
    """Retrieve secrets from AWS Secrets Manager.
    
    Returns:
        dict: The secrets containing TERM_CODE and CHECK_INTERVAL.
        
    Raises:
        Exception: If secrets cannot be retrieved.
    """
    try:
        client = boto3.client(service_name='secretsmanager', region_name='us-east-1')
        get_secret_value_response = client.get_secret_value(SecretId='reapergt-secrets-secrets')
        return json.loads(get_secret_value_response['SecretString'])
    except Exception as e:
        print(f'Error getting secrets: {e}')
        raise

secrets = get_secrets()
TERM = secrets['TERM_CODE']
CHECK_INTERVAL = secrets['CHECK_INTERVAL']

ENDPOINT = 'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in=%s&crn_in=%s'

MAX_RUNTIME = 780

_NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)
_TABLE_RE = re.compile(r'<table[^>]*summary=["\']This layout table is used to present the seating numbers\.["\'][^>]*>(.*?)</table>', re.IGNORECASE | re.DOTALL)
_TD_RE = re.compile(r'<td[^>]*class=["\']dddefault["\'][^>]*>([^<]+)</td>', re.IGNORECASE)

dynamodb = boto3.resource('dynamodb')
crns = dynamodb.Table('reapergt-dynamo-crns')

sqs = boto3.client('sqs')
notify_queue_url = 'https://sqs.us-east-1.amazonaws.com/488900830026/reapergt-sqs-notifqueue'

def lambda_handler(event, context):
    """Handle the Lambda event to scrape course availability.
    
    Args:
        event (dict): The Lambda event.
        context (object): The Lambda context.
        
    Returns:
        dict: Response with status code and body.
    """
    start_time = time.time()
    print('Starting scraper with internal loop')
    
    while (time.time() - start_time) < MAX_RUNTIME:
        try:
            loop_start = time.time()
            
            db_start = time.time()
            response = crns.scan()
            crns_list = {item['crn'] for item in response.get('Items', [])}
            db_time = time.time() - db_start
            print(f'DynamoDB scan took {db_time:.2f}s for {len(crns_list)} CRNs')
            
            if not crns_list:
                print('No CRNs found to process')
            else:
                print(f'Processing {len(crns_list)} CRNs')
                scrape_start = time.time()
                asyncio.run(process_crns(crns_list))
                scrape_time = time.time() - scrape_start
                print(f'Scraping took {scrape_time:.2f}s for {len(crns_list)} CRNs')
            
            loop_time = time.time() - loop_start
            print(f'Total loop time: {loop_time:.2f}s')
            
            remaining_time = MAX_RUNTIME - (time.time() - start_time)
            if remaining_time < CHECK_INTERVAL:
                print(f'Not enough time for another check (need {CHECK_INTERVAL}s, have {remaining_time:.2f}s)')
                break
                
            print(f'Sleeping for {CHECK_INTERVAL}s')
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f'Error in scraper loop: {e}')
            time.sleep(5)
    
    total_time = time.time() - start_time
    print(f'Scraper finished after {total_time:.2f}s')
    return {'statusCode': 200, 'body': 'Success'}

async def process_crns(crns_list: Set[str]) -> None:
    """Process multiple CRNs concurrently.
    
    Args:
        crns_list (Set[str]): Set of CRNs to process.
    """
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=50)) as session:
        tasks = [fetch_course_data(session, crn) for crn in crns_list]
        results = await asyncio.gather(*tasks)
        
        for crn, (name, data) in results:
            if not name or not data:
                print(f'Failed to parse course data for CRN: {crn}')
                continue
                
            if len(name) < 4:
                print(f'Invalid course name format for CRN: {crn}')
                continue

            try:
                # Determine if course is open based on seat availability
                isOpen = len(data) >= 3 and int(data[2]) > 0
                
                crns.update_item(
                    Key={'crn': crn},
                    UpdateExpression='SET course_name = :course_name, course_id = :course_id, course_section = :course_section, isOpen = :isOpen',
                    ExpressionAttributeValues={
                        ':course_name': '%s' % (name[0]),
                        ':course_id': '%s' % (name[2]),
                        ':course_section': '%s' % (name[3]),
                        ':isOpen': isOpen
                    }
                )
                
                if isOpen:
                    sqs.send_message(
                        QueueUrl=notify_queue_url,
                        MessageBody=json.dumps(crn)
                    )
            except Exception as e:
                print(f'Error processing results for CRN {crn}: {e}')

async def fetch_course_data(session: aiohttp.ClientSession, crn: str) -> Tuple[str, Union[Tuple[List[str], List[str]], Tuple[None, None]]]:
    """Fetch and parse course data for a single CRN.
    
    Args:
        session (aiohttp.ClientSession): The HTTP session to use.
        crn (str): The CRN to fetch data for.
        
    Returns:
        Tuple[str, Union[Tuple[List[str], List[str]], Tuple[None, None]]]: The CRN and its parsed data.
    """
    url = ENDPOINT % (TERM, crn)
    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f'HTTP Error {response.status} fetching course data for CRN {crn}')
                return crn, (None, None)
            
            html = await response.text()
            return crn, parse_course_regex(html)
    except Exception as e:
        print(f'Error fetching course data for CRN {crn}: {e}')
        return crn, (None, None)

def parse_course_regex(html: str) -> Tuple[Union[List[str], None], Union[List[str], None]]:
    """Parse course data from HTML using regex.
    
    Args:
        html (str): The HTML to parse.
        
    Returns:
        Tuple[Union[List[str], None], Union[List[str], None]]: The parsed course name and data.
    """
    m_name = _NAME_RE.search(html)
    if not m_name:
        return None, None
    name = [part.strip().replace('<br />', '').replace('<br>', '') for part in m_name.group(1).split(" - ")]

    m_table = _TABLE_RE.search(html)
    if not m_table:
        return name, []
    snippet = m_table.group(1)
    data = _TD_RE.findall(snippet)
    return name, data
