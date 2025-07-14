import json
import boto3
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

def handler(event, context):
    """
    Notifier Lambda function
    Triggered directly by scraper Lambda
    Sends SMS notifications when course spots are available
    """
    try:
        logger.info("🚀 NOTIFIER STARTED")
        logger.info(f"📋 Processing notification event: {event}")
        
        # Process the direct invocation event
        if event.get('notification_type') == 'course_available':
            crn = event.get('crn')
            availability = event.get('availability')
            
            logger.info(f"🎯 Processing course_available notification for CRN {crn}")
            # Send SMS notifications to all users tracking this CRN
            send_sms_notifications(crn, availability)
            logger.info(f"✅ SMS notifications completed for CRN {crn}")
            
            # Check quota and warn if low
            check_textbelt_quota_and_warn()
        else:
            logger.warning(f"❌ Unknown notification type: {event.get('notification_type')}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification sent successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in notifier: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Notification failed',
                'details': str(e)
            })
        }

def get_secrets():
    """Get secrets from AWS Secrets Manager"""
    try:
        secret_name = "reaper-secrets"
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Error getting secrets: {str(e)}")
        raise

def get_users_tracking_crn(crn):
    """Get all users who are tracking this CRN and have phone numbers using normalized structure"""
    try:
        users_table = dynamodb.Table(os.environ.get('DYNAMODB_USERS_TABLE', 'reaper-users'))
        crns_table = dynamodb.Table(os.environ.get('DYNAMODB_CRNS_TABLE', 'reaper-crns'))
        
        # Get the CRN record to find users tracking it
        crn_response = crns_table.get_item(Key={'crn': crn})
        if 'Item' not in crn_response:
            logger.warning(f"CRN {crn} not found in CRNs table")
            return []
        
        tracking_users = crn_response['Item'].get('users', [])
        users_with_phone = []
        
        # Get phone numbers for users tracking this CRN
        for user_id in tracking_users:
            try:
                user_response = users_table.get_item(Key={'user_id': user_id})
                if 'Item' in user_response:
                    user_item = user_response['Item']
                    phone_number = user_item.get('phone_number')
                    
                    # Check if user has phone number and is still tracking this CRN
                    if phone_number and crn in user_item.get('crns', []):
                        users_with_phone.append({
                            'user_id': user_id,
                            'phone_number': phone_number
                        })
            except Exception as e:
                logger.error(f"Error getting user {user_id} data: {str(e)}")
        
        logger.info(f"Found {len(users_with_phone)} users tracking CRN {crn} with phone numbers")
        return users_with_phone
        
    except Exception as e:
        logger.error(f"Error getting users for CRN {crn}: {str(e)}")
        return []

def send_sms_notifications(crn, availability):
    """Send SMS notifications to users tracking this CRN"""
    try:
        users = get_users_tracking_crn(crn)
        if not users:
            logger.info(f"No users with phone numbers tracking CRN {crn}")
            return
        
        course_name = availability.get('course_name', f'CRN {crn}')
        seats_remaining = availability.get('seats_remaining', 0)
        
        # Create concise SMS message with professional emoji and better formatting
        message = f"🎓 COURSE AVAILABLE 🎓\n\n{course_name} - (CRN {crn})\nSeats open: {seats_remaining}\n\nRegister in OSCAR and update your courses in the Reaper app"
        
        logger.info(f'Sending SMS to {len(users)} users for CRN {crn}: "{message}"')
        
        successful_sends = 0
        failed_sends = 0
        
        for user in users:
            try:
                # Format phone number (ensure it starts with +1 for US numbers)
                phone = user['phone_number']
                if not phone.startswith('+'):
                    if phone.startswith('1'):
                        phone = '+' + phone
                    else:
                        phone = '+1' + phone
                
                # Send SMS using Textbelt
                import requests
                
                api_key = os.environ.get('TEXTBELT_API_KEY')
                if not api_key:
                    logger.error("TEXTBELT_API_KEY not configured")
                    failed_sends += 1
                    continue
                
                # Clean phone number (remove +1 if present)
                clean_phone = phone.replace('+1', '').replace('+', '')
                
                response = requests.post('https://textbelt.com/text', {
                    'phone': clean_phone,
                    'message': message,
                    'key': api_key
                }, timeout=10)
                
                result = response.json()
                
                if not result.get('success'):
                    logger.error(f'Textbelt SMS failed for user {user["user_id"]}: {result}')
                    failed_sends += 1
                    continue
                
                logger.info(f'Successfully sent SMS to user {user["user_id"]} at {phone} for CRN {crn}')
                successful_sends += 1
                
                # Mark user as notified for this CRN (so they don't get multiple SMS)
                mark_user_notified(user['user_id'], crn)
                
            except Exception as e:
                logger.error(f'Error sending SMS to user {user["user_id"]}: {e}')
                failed_sends += 1
        
        logger.info(f'SMS notification summary for CRN {crn}: {successful_sends} successful, {failed_sends} failed')
        
    except Exception as e:
        logger.error(f"Error sending SMS notifications: {str(e)}")
        raise

def mark_user_notified(user_id, crn):
    """Mark that a user has been notified for this CRN to prevent duplicate SMS"""
    try:
        users_table = dynamodb.Table(os.environ.get('DYNAMODB_USERS_TABLE', 'reaper-users'))
        
        # Get current user data
        response = users_table.get_item(Key={'user_id': user_id})
        user_item = response.get('Item', {})
        
        # Add to notified_crns list
        notified_crns = user_item.get('notified_crns', [])
        if crn not in notified_crns:
            notified_crns.append(crn)
            user_item['notified_crns'] = notified_crns
            
            users_table.put_item(Item=user_item)
            logger.info(f"Marked user {user_id} as notified for CRN {crn}")
            
    except Exception as e:
        logger.error(f"Error marking user {user_id} as notified for CRN {crn}: {str(e)}")

def check_textbelt_quota_and_warn():
    """Check Textbelt quota and send warning if low"""
    try:
        import requests
        
        api_key = os.environ.get('TEXTBELT_API_KEY')
        if not api_key:
            logger.warning("TEXTBELT_API_KEY not configured for quota check")
            return
        
        # Check quota using Textbelt status endpoint
        response = requests.post('https://textbelt.com/status', {
            'key': api_key
        }, timeout=10)
        
        result = response.json()
        quota_remaining = result.get('quotaRemaining', 0)
        
        logger.info(f"Textbelt quota remaining: {quota_remaining}")
        
        # Send warning if quota is low (less than 100 messages)
        if quota_remaining <= 100:
            admin_phone = "4085816547"  # Your phone number
            warning_message = f"🚨 REAPER ALERT 🚨\n\nTextbelt SMS quota is LOW!\nRemaining: {quota_remaining} messages\n\nAdd more credits at textbelt.com"
            
            # Send warning SMS
            warning_response = requests.post('https://textbelt.com/text', {
                'phone': admin_phone,
                'message': warning_message,
                'key': api_key
            }, timeout=10)
            
            warning_result = warning_response.json()
            
            if warning_result.get('success'):
                logger.info(f"Successfully sent quota warning to admin. Remaining: {quota_remaining}")
            else:
                logger.error(f"Failed to send quota warning: {warning_result}")
        
    except Exception as e:
        logger.error(f"Error checking Textbelt quota: {e}")