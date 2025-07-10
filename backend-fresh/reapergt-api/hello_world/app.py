import json
import boto3
import re
import requests
import base64
import os
from typing import Dict, Any, List

def get_cors_headers():
    """Get CORS headers for all responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
    }

def validate_google_jwt(token: str) -> str:
    """Validate Google JWT token and extract user ID."""
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Decode JWT token (basic validation for now)
        parts = token.split('.')
        if len(parts) != 3:
            raise Exception("Invalid JWT format")
        
        # Decode the payload
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded_payload)
        
        # Basic validation
        if 'sub' not in claims:
            raise Exception("Missing user ID in token")
        
        if 'iss' not in claims or claims['iss'] not in ['https://accounts.google.com', 'accounts.google.com']:
            raise Exception("Invalid token issuer")
        
        return claims['sub']
        
    except Exception as e:
        print(f"Error validating Google JWT: {e}")
        raise Exception("Invalid or expired token")

def validate_crn_format(crn: str) -> bool:
    """Validate CRN format (5 digits)."""
    return bool(re.match(r'^\d{5}$', crn))

def check_crn_exists(crn: str) -> Dict[str, Any]:
    """Check if CRN exists and if it's open by scraping OSCAR."""
    try:
        # Use hardcoded term for now (Spring 2025)
        term = "202508"
        
        url = f'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in={term}&crn_in={crn}'
        print(f"Checking URL: {url}")
        
        # Regex patterns for parsing
        _NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)
        _SEATS_RE = re.compile(r'Seats</th>\s*<td[^>]*>(\d+)</td>', re.IGNORECASE | re.DOTALL)
        _REMAINING_RE = re.compile(r'Remaining</th>\s*<td[^>]*>(\d+)</td>', re.IGNORECASE | re.DOTALL)
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        html = response.text
        if _NAME_RE.search(html) is None:
            return {
                'exists': False,
                'error': 'CRN does not exist'
            }
        
        # Extract course information
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
        
        # Check seat availability
        is_open = False
        seats_remaining = 0
        total_seats = 0
        
        # Try to find seat information
        seats_match = _SEATS_RE.search(html)
        remaining_match = _REMAINING_RE.search(html)
        
        if seats_match and remaining_match:
            total_seats = int(seats_match.group(1))
            seats_remaining = int(remaining_match.group(1))
            is_open = seats_remaining > 0
            print(f"CRN {crn}: {seats_remaining}/{total_seats} seats available")
        else:
            print(f"Could not parse seat information for CRN {crn}")
            # Default to closed if we can't parse seats
            is_open = False
        
        return {
            'exists': True,
            'course_info': {
                'course_name': course_name,
                'course_id': course_id,
                'course_section': course_section,
                'is_open': is_open,
                'seats_remaining': seats_remaining,
                'total_seats': total_seats
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

# DynamoDB functions
def get_dynamodb_table(table_name: str):
    """Get DynamoDB table resource."""
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(table_name)

def get_user_crns(user_id: str) -> List[Dict[str, Any]]:
    """Get all CRNs for a user."""
    try:
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        print(f"Getting CRNs for user: {user_id}")
        response = users_table.get_item(Key={'user_id': user_id})
        print(f"DynamoDB response: {response}")
        
        if 'Item' not in response:
            print(f"No user found with ID: {user_id}")
            return []
        
        crn_list = response['Item'].get('crns', [])
        print(f"Found {len(crn_list)} CRNs for user: {crn_list}")
        return crn_list
        
    except Exception as e:
        print(f"Error getting user CRNs: {e}")
        return []

def add_crn_to_user(user_id: str, crn: str, course_info: Dict[str, Any]) -> Dict[str, Any]:
    """Add CRN to user's list."""
    try:
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        crns_table = get_dynamodb_table(os.environ['DYNAMODB_CRNS_TABLE'])
        
        print(f"Adding CRN {crn} for user: {user_id}")
        
        # Get current user data
        response = users_table.get_item(Key={'user_id': user_id})
        print(f"Current user data: {response}")
        current_crns = response.get('Item', {}).get('crns', [])
        print(f"Current CRNs: {current_crns}")
        
        # Check if CRN already exists
        for existing_crn in current_crns:
            if existing_crn['crn'] == crn:
                print(f"CRN {crn} already exists for user {user_id}")
                return {'error': 'CRN already exists in your list'}
        
        # Add new CRN
        new_crn_data = {
            'crn': crn,
            'course_name': course_info['course_name'],
            'course_id': course_info['course_id'],
            'course_section': course_info['course_section'],
            'isOpen': course_info.get('is_open', False),
            'seats_remaining': course_info.get('seats_remaining', 0),
            'total_seats': course_info.get('total_seats', 0)
        }
        
        current_crns.append(new_crn_data)
        print(f"Updated CRNs list: {current_crns}")
        
        # Update user's CRN list
        users_table.put_item(Item={
            'user_id': user_id,
            'crns': current_crns
        })
        print(f"Successfully stored user CRNs in users table")
        
        # Update global CRN tracking
        crns_table.put_item(Item={
            'crn': crn,
            'users': [user_id]
        })
        print(f"Successfully stored CRN {crn} in crns table")
        
        return new_crn_data
        
    except Exception as e:
        print(f"Error adding CRN: {e}")
        return {'error': 'Failed to add CRN'}

def remove_crn_from_user(user_id: str, crn: str) -> Dict[str, Any]:
    """Remove CRN from user's list."""
    try:
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        crns_table = get_dynamodb_table(os.environ['DYNAMODB_CRNS_TABLE'])
        
        # Get current user data
        response = users_table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            return {'error': 'User not found'}
        
        current_crns = response['Item'].get('crns', [])
        
        # Remove CRN from user's list
        updated_crns = [c for c in current_crns if c['crn'] != crn]
        
        if len(updated_crns) == len(current_crns):
            return {'error': 'CRN not found in your list'}
        
        # Update user's CRN list
        users_table.put_item(Item={
            'user_id': user_id,
            'crns': updated_crns
        })
        
        # Remove user from global CRN tracking
        try:
            crns_table.delete_item(Key={'crn': crn})
        except:
            pass  # Ignore if CRN doesn't exist in global table
        
        return {'message': 'CRN removed successfully'}
        
    except Exception as e:
        print(f"Error removing CRN: {e}")
        return {'error': 'Failed to remove CRN'}

def lambda_handler(event, context):
    """API Lambda function to handle CRN requests"""
    print(f"Event: {event}")
    
    # Extract method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/').rstrip('/')
    
    # Handle preflight OPTIONS request for all paths
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'message': 'CORS preflight successful'})
        }
    
    # Extract authorization header
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    if not auth_header:
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Missing authorization header'})
        }
    
    # Validate JWT token
    try:
        user_id = validate_google_jwt(auth_header)
    except Exception as e:
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }
    
    # Handle different endpoints
    if path == '/crns':
        if http_method == 'GET':
            # Get user's CRNs
            crns = get_user_crns(user_id)
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps(crns)
            }
            
        elif http_method == 'POST':
            # Add new CRN
            try:
                body = json.loads(event.get('body', '{}'))
                crn = body.get('crn', '').strip()
                
                if not crn:
                    return {
                        'statusCode': 400,
                        'headers': get_cors_headers(),
                        'body': json.dumps({'error': 'CRN is required'})
                    }
                
                if not validate_crn_format(crn):
                    return {
                        'statusCode': 400,
                        'headers': get_cors_headers(),
                        'body': json.dumps({'error': 'Invalid CRN format. Must be 5 digits.'})
                    }
                
                # Check if CRN exists on OSCAR
                crn_check = check_crn_exists(crn)
                if not crn_check['exists']:
                    return {
                        'statusCode': 404,
                        'headers': get_cors_headers(),
                        'body': json.dumps({'error': crn_check['error']})
                    }
                
                # Add CRN to user's list
                result = add_crn_to_user(user_id, crn, crn_check['course_info'])
                
                if 'error' in result:
                    return {
                        'statusCode': 400,
                        'headers': get_cors_headers(),
                        'body': json.dumps(result)
                    }
                
                return {
                    'statusCode': 201,
                    'headers': get_cors_headers(),
                    'body': json.dumps(result)
                }
                
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
            except Exception as e:
                print(f"Error in POST /crns: {e}")
                return {
                    'statusCode': 500,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Internal server error'})
                }
    
    elif path.startswith('/crns/'):
        # Extract CRN from path
        crn = path.split('/')[-1]
        
        if http_method == 'DELETE':
            # Remove CRN
            result = remove_crn_from_user(user_id, crn)
            
            if 'error' in result:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps(result)
                }
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps(result)
            }
    
    # Default response for unknown paths
    return {
        'statusCode': 404,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': 'Not found'})
    }
