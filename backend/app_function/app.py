import json
import boto3
import re
import requests
import base64
import os
from decimal import Decimal
from typing import Dict, Any, List

def convert_decimals(obj):
    """Convert Decimal objects to int/float for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def get_secrets():
    """Retrieve secrets from AWS Secrets Manager."""
    try:
        client = boto3.client(service_name='secretsmanager', region_name='us-east-1')
        get_secret_value_response = client.get_secret_value(SecretId='reaper-secrets')
        return json.loads(get_secret_value_response['SecretString'])
    except Exception as e:
        print(f'Error getting secrets: {e}')
        return {}

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
        
        # Regex patterns for parsing (updated to match actual HTML structure)
        _NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)
        # Updated to handle SPAN tags and parse the seats row: Capacity, Actual, Remaining
        _SEATS_ROW_RE = re.compile(r'<SPAN[^>]*>Seats</SPAN></th>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>(\d+)</td>', re.IGNORECASE | re.DOTALL)
        
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
        
        # Try to find seat information using the updated regex
        seats_row_match = _SEATS_ROW_RE.search(html)
        
        if seats_row_match:
            total_seats = int(seats_row_match.group(1))  # Capacity
            actual_enrolled = int(seats_row_match.group(2))  # Actual
            seats_remaining = int(seats_row_match.group(3))  # Remaining
            is_open = seats_remaining > 0
            print(f"CRN {crn}: {seats_remaining}/{total_seats} seats available (actual enrolled: {actual_enrolled})")
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

def register_push_notification(user_id: str, body: str) -> Dict[str, Any]:
    """Register push notification subscription for user."""
    try:
        # Parse request body
        request_data = json.loads(body)
        push_subscription = request_data.get('push_subscription')
        
        if not push_subscription:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Push subscription data is required'})
            }
        
        # Get current user data
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        user_response = users_table.get_item(Key={'user_id': user_id})
        user_item = user_response.get('Item', {})
        
        # Update user with push subscription info
        user_item['user_id'] = user_id
        user_item['push_subscription'] = push_subscription
        user_item['crns'] = user_item.get('crns', [])
        
        users_table.put_item(Item=user_item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Push notification registration successful'
            })
        }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Failed to register push notification for {user_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to register push notification: {str(e)}'})
        }

def register_phone_number(user_id: str, body: str) -> Dict[str, Any]:
    """Register phone number for SMS notifications."""
    try:
        # Parse request body
        request_data = json.loads(body)
        phone_number = request_data.get('phone_number', '').strip()
        
        if not phone_number:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Phone number is required'})
            }
        
        # Basic phone number validation
        import re
        # Remove all non-digits
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Check if it's a valid US phone number (10 or 11 digits)
        if len(digits_only) == 10:
            formatted_phone = f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            formatted_phone = f"+{digits_only}"
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid phone number format. Please use a US phone number.'})
            }
        
        # Get current user data
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        user_response = users_table.get_item(Key={'user_id': user_id})
        user_item = user_response.get('Item', {})
        
        # Update user with phone number
        user_item['user_id'] = user_id
        user_item['phone_number'] = formatted_phone
        user_item['crns'] = user_item.get('crns', [])
        
        users_table.put_item(Item=user_item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Phone number registered successfully for SMS notifications',
                'phone_number': formatted_phone
            })
        }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Failed to register phone number for {user_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to register phone number: {str(e)}'})
        }

def send_test_sms_notification(user_id: str, crn: str, course_info: Dict[str, Any]) -> Dict[str, Any]:
    """Send a test SMS notification when a CRN is added."""
    try:
        # Get user's phone number from database
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        user_response = users_table.get_item(Key={'user_id': user_id})
        user_data = user_response.get('Item', {})
        
        phone_number = user_data.get('phone_number')
        if not phone_number:
            print(f"No phone number found for user {user_id}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No phone number registered. Please add your phone number in settings.'})
            }
        
        # Create test SMS message
        course_name = course_info.get('course_name', f'CRN {crn}')
        seats_remaining = course_info.get('seats_remaining', 0)
        total_seats = course_info.get('total_seats', 0)
        
        message = f"📚 TEST: Course Added Successfully!\n\n{course_name}\nCRN: {crn}\nSeats: {seats_remaining}/{total_seats}\n\nYou'll get SMS alerts when this course opens up! 🎉"
        
        # Send SMS using AWS SNS
        import boto3
        sns_client = boto3.client('sns')
        
        try:
            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'Reaper'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            print(f'Successfully sent test SMS to user {user_id} at {phone_number}')
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Test SMS sent successfully!'
                })
            }
            
        except Exception as e:
            print(f'SNS error sending test SMS: {e}')
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send test SMS'})
            }
    
    except Exception as e:
        print(f"Failed to send test SMS for {user_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to send test SMS: {str(e)}'})
        }

def send_test_push_notification(user_id: str) -> Dict[str, Any]:
    """Send a test push notification to the user."""
    try:
        # Get user's push subscription from database
        users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
        user_response = users_table.get_item(Key={'user_id': user_id})
        user_data = user_response.get('Item', {})
        
        if 'push_subscription' not in user_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No push subscription found. Please enable notifications first.'})
            }
        
        push_subscription = user_data['push_subscription']
        
        # Create test notification payload
        notification_payload = {
            'title': '🧪 Test Notification',
            'body': 'Your notifications are working! You\'ll get alerts when courses open up.',
            'icon': '/logo.png',
            'badge': '/logo.png',
            'data': {
                'test': True,
                'url': '/'
            },
            'tag': 'test-notification',
            'requireInteraction': False
        }
        
        # Get VAPID keys from secrets
        secrets = get_secrets()
        vapid_private_key = secrets.get('VAPID_PRIVATE_KEY')
        vapid_public_key = secrets.get('VAPID_PUBLIC_KEY')
        
        if not vapid_private_key or not vapid_public_key:
            print('VAPID keys not found in secrets')
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Server configuration error'})
            }
        
        # Send the notification using pywebpush
        try:
            from pywebpush import webpush, WebPushException
            
            response = webpush(
                subscription_info=push_subscription,
                data=json.dumps(notification_payload),
                vapid_private_key=vapid_private_key,
                vapid_claims={
                    "sub": "mailto:support@getreaper.com",
                    "aud": push_subscription['endpoint']
                }
            )
            
            print(f'Successfully sent test notification to user {user_id}')
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Test notification sent successfully!'
                })
            }
            
        except WebPushException as e:
            print(f'WebPush error sending test notification: {e}')
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send test notification'})
            }
        except Exception as e:
            print(f'Error sending test notification: {e}')
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send test notification'})
            }
    
    except Exception as e:
        print(f"Failed to send test notification for {user_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to send test notification: {str(e)}'})
        }

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
    
    # Health check endpoint (no auth required)
    if path == '/health':
        if http_method == 'GET':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'Reaper API',
                    'version': '1.0.0',
                    'timestamp': context.aws_request_id if context else 'local'
                })
            }
    
    # Extract authorization header for authenticated endpoints
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
            # Convert Decimal objects to int/float for JSON serialization
            crns_converted = convert_decimals(crns)
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps(crns_converted)
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
                
                # Send test SMS notification when course is added
                try:
                    test_sms_result = send_test_sms_notification(user_id, crn, crn_check['course_info'])
                    print(f"Test SMS notification result: {test_sms_result}")
                except Exception as e:
                    print(f"Failed to send test SMS notification: {e}")
                
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
    
    elif path == '/register-push':
        if http_method == 'POST':
            # Register push notification subscription (legacy)
            result = register_push_notification(user_id, event.get('body', '{}'))
            return {
                'statusCode': result['statusCode'],
                'headers': get_cors_headers(),
                'body': result['body']
            }
    
    elif path == '/register-phone':
        if http_method == 'POST':
            # Register phone number for SMS notifications
            result = register_phone_number(user_id, event.get('body', '{}'))
            return {
                'statusCode': result['statusCode'],
                'headers': get_cors_headers(),
                'body': result['body']
            }
    
    elif path == '/test-notification':
        if http_method == 'POST':
            # Send test notification
            result = send_test_push_notification(user_id)
            return {
                'statusCode': result['statusCode'],
                'headers': get_cors_headers(),
                'body': result['body']
            }
    
    elif path == '/refresh':
        if http_method == 'POST':
            # Manually refresh all user's CRNs
            try:
                crns = get_user_crns(user_id)
                updated_crns = []
                
                for crn_data in crns:
                    crn = crn_data.get('crn')
                    if crn:
                        # Check current availability
                        crn_check = check_crn_exists(crn)
                        if crn_check.get('exists'):
                            course_info = crn_check['course_info']
                            # Update the CRN data
                            crn_data.update({
                                'isOpen': course_info.get('is_open', False),
                                'seats_remaining': course_info.get('seats_remaining', 0),
                                'total_seats': course_info.get('total_seats', 0),
                                'course_name': course_info.get('course_name', crn_data.get('course_name')),
                                'course_id': course_info.get('course_id', crn_data.get('course_id')),
                                'course_section': course_info.get('course_section', crn_data.get('course_section')),
                            })
                    updated_crns.append(crn_data)
                
                # Update user's CRN list
                users_table = get_dynamodb_table(os.environ['DYNAMODB_USERS_TABLE'])
                users_table.put_item(Item={
                    'user_id': user_id,
                    'crns': updated_crns
                })
                
                return {
                    'statusCode': 200,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'message': 'CRNs refreshed successfully',
                        'crns': convert_decimals(updated_crns)
                    })
                }
                
            except Exception as e:
                print(f"Error refreshing CRNs: {e}")
                return {
                    'statusCode': 500,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Failed to refresh CRNs'})
                }
    
    # Default response for unknown paths
    return {
        'statusCode': 404,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': 'Not found'})
    }
