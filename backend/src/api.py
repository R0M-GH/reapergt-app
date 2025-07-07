import boto3
import json
import re
import requests
from typing import Dict, Any, List

def get_secrets():
    """Retrieve secrets from AWS Secrets Manager.
    
    Returns:
        dict: The secrets containing TERM_CODE.
        
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

def validate_crn_format(crn: str) -> bool:
    """Validate CRN format (5 digits)."""
    return bool(re.match(r'^\d{5}$', crn))

def check_crn_exists(crn: str) -> Dict[str, Any]:
    """Check if CRN exists by scraping OSCAR using the exact same logic as console.py."""
    try:
        # Try to get term from secrets, fallback to environment variable for local testing
        try:
            secrets = get_secrets()
            term = secrets['TERM_CODE']
            print(f"Using TERM_CODE from secrets: {term}")
        except Exception as e:
            print(f"Failed to get secrets, using fallback: {e}")
            # Fallback for local testing - you can change this to the current term
            term = "202508"  # Fall 2025 - change this to match your test CRN
            print(f"Using fallback TERM_CODE: {term}")
        
        url = f'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in={term}&crn_in={crn}'
        print(f"Checking URL: {url}")
        
        # Use the exact same regex pattern as console.py
        _NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        html = response.text
        if _NAME_RE.search(html) is None:
            return {
                'exists': False,
                'error': 'CRN does not exist'
            }
        
        name_match = _NAME_RE.search(html)
        if name_match:
            name = [part.strip().replace('<br />', '').replace('<br>', '') for part in name_match.group(1).split(" - ")]
            
            if len(name) >= 4:
                course_name = name[0]
                course_id = name[2]
                course_section = name[3]
            else:
                # Fallback if parsing fails
                course_name = name_match.group(1)
                course_id = 'N/A'
                course_section = 'N/A'
        else:
            return {
                'exists': False,
                'error': 'Could not extract course information'
            }
        
        return {
            'exists': True,
            'course_info': {
                'course_name': course_name,
                'course_id': course_id,
                'course_section': course_section
            }
        }
        
    except requests.RequestException as e:
        print(f"Request error checking CRN {crn}: {e}")
        return {
            'exists': False,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        print(f"Error checking CRN {crn}: {e}")
        return {
            'exists': False,
            'error': f'Unexpected error: {str(e)}'
        }

def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for all responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # TEMPORARILY DISABLED FOR LOCAL TESTING
        # Extract user ID from Cognito JWT
        # user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # For local testing, use a dummy user ID
        user_id = 'local-test-user'
        print(f"Using dummy user ID for local testing: {user_id}")
        
        http_method = event['httpMethod']
        path = event['path']
        
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        users_table = dynamodb.Table('reapergt-dynamo-users')
        crns_table = dynamodb.Table('reapergt-dynamo-crns')
        
        # CORS preflight handler
        if http_method == 'OPTIONS':
            print(f"CORS preflight for path: {path}")
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Route to appropriate handler based on path and method
        if http_method == 'GET' and path == '/crns':
            return get_user_crns(users_table, crns_table, user_id)
        
        elif http_method == 'POST' and path == '/crns':
            return add_crn(users_table, crns_table, user_id, event['body'])
        
        elif http_method == 'DELETE' and path.startswith('/crns/'):
            crn = path.split('/')[-1]
            return remove_crn(users_table, crns_table, user_id, crn)
        
        elif http_method == 'GET' and path.startswith('/crn/'):
            crn = path.split('/')[-1]
            return get_crn_info(crns_table, crn)
        
        elif http_method == 'POST' and path == '/register-push':
            return register_push_notification(users_table, user_id, event['body'])
        
        else:
            print(f"Endpoint not found: {http_method} {path}")
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_user_crns(users_table, crns_table, user_id: str) -> Dict[str, Any]:
    try:
        response = users_table.get_item(Key={'user_id': user_id})
        crns = list(response.get('Item', {}).get('crns', set()))
        print(f"User {user_id} tracked CRNs: {crns}")
        
        crn_objs = []
        for crn in crns:
            crn_info = crns_table.get_item(Key={'crn': crn})
            item = crn_info.get('Item', {})
            crn_objs.append({
                'crn': crn,
                'course_id': item.get('course_id', ''),
                'course_name': item.get('course_name', ''),
                'course_section': item.get('course_section', ''),
                'isOpen': item.get('isOpen', False)
            })
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'crns': crn_objs})
        }
    except Exception as e:
        print(f"Failed to retrieve CRNs for {user_id}: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Failed to retrieve CRNs: {str(e)}'})
        }

def add_crn(users_table, crns_table, user_id: str, body: str) -> Dict[str, Any]:
    """POST /crns - Add a CRN to the authenticated user's tracked list."""
    try:
        # Parse request body
        request_data = json.loads(body)
        crn = request_data.get('crn')
        
        if not crn:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'CRN is required'})
            }
        
        # Validate CRN format
        if not validate_crn_format(crn):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid CRN format. Must be 5 digits.'})
            }
        
        # Check if user already has 5 CRNs
        user_response = users_table.get_item(Key={'user_id': user_id})
        current_crns = set(user_response.get('Item', {}).get('crns', set()))
        
        if len(current_crns) >= 5:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Maximum of 5 CRNs allowed per user'})
            }
        
        # Check if CRN already exists in user's list
        if crn in current_crns:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'CRN already in your tracked list'})
            }
        
        # Check if CRN exists in OSCAR and scrape course info
        crn_check = check_crn_exists(crn)
        if not crn_check['exists']:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': f'CRN not found: {crn_check.get("error", "Unknown error")}'})
            }
        
        # Check seat availability to determine if course is open
        isOpen = False
        try:
            import re
            # Get term code
            try:
                secrets = get_secrets()
                term = secrets['TERM_CODE']
            except Exception:
                term = "202508"
            
            url = f'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in={term}&crn_in={crn}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            html = response.text
            _TABLE_RE = re.compile(r'<table[^>]*summary=["\']This layout table is used to present the seating numbers\.["\'][^>]*>(.*?)</table>', re.IGNORECASE | re.DOTALL)
            _TD_RE = re.compile(r'<td[^>]*class=["\']dddefault["\'][^>]*>([^<]+)</td>', re.IGNORECASE)
            
            m_table = _TABLE_RE.search(html)
            if m_table:
                snippet = m_table.group(1)
                data = _TD_RE.findall(snippet)
                if len(data) >= 3 and int(data[2]) > 0:
                    isOpen = True
        except Exception as e:
            print(f"Error checking seat availability for CRN {crn}: {e}")
            isOpen = False
        
        # Add CRN to user's list
        current_crns.add(crn)
        users_table.put_item(Item={
            'user_id': user_id,
            'crns': current_crns
        })
        
        # Update CRN table with course info, user, and isOpen status
        course_info = crn_check['course_info']
        crn_response = crns_table.get_item(Key={'crn': crn})
        existing_user_ids = set(crn_response.get('Item', {}).get('user_ids', set()))
        existing_user_ids.add(user_id)
        
        crns_table.put_item(Item={
            'crn': crn,
            'course_id': course_info['course_id'],
            'course_name': course_info['course_name'],
            'course_section': course_info['course_section'],
            'user_ids': existing_user_ids,
            'isOpen': isOpen
        })
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'CRN added successfully',
                'crn': crn,
                'course_info': course_info,
                'isOpen': isOpen
            })
        }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Failed to add CRN for {user_id}: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Failed to add CRN: {str(e)}'})
        }

def remove_crn(users_table, crns_table, user_id: str, crn: str) -> Dict[str, Any]:
    """DELETE /crns/{crn} - Remove a CRN from the authenticated user's tracked list."""
    try:
        # Validate CRN format
        if not validate_crn_format(crn):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid CRN format. Must be 5 digits.'})
            }
        
        # Get current user CRNs
        user_response = users_table.get_item(Key={'user_id': user_id})
        current_crns = set(user_response.get('Item', {}).get('crns', set()))
        
        if crn not in current_crns:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': f'CRN {crn} not found in your tracked list'})
            }
        
        # Remove CRN from user's set
        current_crns.remove(crn)
        
        # Handle empty set - delete user record if no CRNs left
        if not current_crns:
            users_table.delete_item(Key={'user_id': user_id})
            print(f"Deleted user {user_id} - no CRNs remaining")
        else:
            users_table.put_item(Item={
                'user_id': user_id,
                'crns': current_crns
            })
        
        # Update CRN table
        crn_response = crns_table.get_item(Key={'crn': crn})
        if 'Item' in crn_response:
            existing_user_ids = set(crn_response['Item'].get('user_ids', set()))
            existing_user_ids.discard(user_id)
            
            if not existing_user_ids:
                # No users tracking this CRN, delete it
                crns_table.delete_item(Key={'crn': crn})
                print(f"Deleted CRN {crn} - no users tracking it")
            else:
                crns_table.put_item(Item={
                    'crn': crn,
                    'course_id': crn_response['Item'].get('course_id', ''),
                    'course_name': crn_response['Item'].get('course_name', ''),
                    'course_section': crn_response['Item'].get('course_section', ''),
                    'user_ids': existing_user_ids
                })
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': f'CRN {crn} removed successfully',
                'remaining_crns': list(current_crns)
            })
        }
    
    except Exception as e:
        print(f"Failed to remove CRN for {user_id}: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Failed to remove CRN: {str(e)}'})
        }

def get_crn_info(crns_table, crn: str) -> Dict[str, Any]:
    try:
        # Validate CRN format
        if not validate_crn_format(crn):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid CRN format. Must be 5 digits.'})
            }
        
        # Get CRN info from DynamoDB
        response = crns_table.get_item(Key={'crn': crn})
        
        if 'Item' not in response:
            # CRN not in database, check OSCAR
            crn_check = check_crn_exists(crn)
            if not crn_check['exists']:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'CRN not found'})
                }
            
            # Return course info from OSCAR
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'crn': crn,
                    'course_info': crn_check['course_info'],
                    'tracked_by': 0
                })
            }
        
        # Return CRN info from database
        item = response['Item']
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'crn': crn,
                'course_info': {
                    'course_id': item.get('course_id', ''),
                    'course_name': item.get('course_name', ''),
                    'course_section': item.get('course_section', '')
                },
                'tracked_by': len(item.get('user_ids', set()))
            })
        }
    
    except Exception as e:
        print(f"Failed to get CRN info for {crn}: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Failed to get CRN info: {str(e)}'})
        }

def register_push_notification(users_table, user_id: str, body: str) -> Dict[str, Any]:
    try:
        # Parse request body
        request_data = json.loads(body)
        push_subscription = request_data.get('push_subscription')
        
        if not push_subscription:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Push subscription data is required'})
            }
        
        # Get current user data
        user_response = users_table.get_item(Key={'user_id': user_id})
        user_item = user_response.get('Item', {})
        
        # Update user with push subscription info
        user_item['user_id'] = user_id
        user_item['push_subscription'] = push_subscription
        user_item['crns'] = user_item.get('crns', set())
        
        users_table.put_item(Item=user_item)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Push notification registration successful'
            })
        }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Failed to register push notification for {user_id}: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Failed to register push notification: {str(e)}'})
        }

