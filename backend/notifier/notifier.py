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

def handler(event, context):
    """
    Notifier Lambda function
    Triggered directly by scraper Lambda
    Sends push notifications when course spots are available
    """
    try:
        logger.info("Notifier started")
        logger.info(f"Processing notification: {event}")
        
        # Process the direct invocation event
        if event.get('notification_type') == 'course_available':
            crn = event.get('crn')
            availability = event.get('availability')
            
            # Send push notifications to all users tracking this CRN
            send_push_notifications(crn, availability)
            logger.info(f"Push notifications sent for CRN {crn}")
        
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
    """Get all users who are tracking this CRN"""
    try:
        users_table = dynamodb.Table(os.environ.get('DYNAMODB_USERS_TABLE', 'reaper-users'))
        
        # Scan all users to find who has this CRN
        response = users_table.scan()
        users_with_push = []
        
        for user_item in response.get('Items', []):
            user_id = user_item.get('user_id')
            crns_list = user_item.get('crns', [])
            push_subscription = user_item.get('push_subscription')
            
            # Check if this user has the CRN and push subscription
            if push_subscription:
                for crn_data in crns_list:
                    if crn_data.get('crn') == crn:
                        users_with_push.append({
                            'user_id': user_id,
                            'push_subscription': push_subscription
                        })
                        break
        
        logger.info(f"Found {len(users_with_push)} users tracking CRN {crn} with push subscriptions")
        return users_with_push
        
    except Exception as e:
        logger.error(f"Error getting users for CRN {crn}: {str(e)}")
        return []

def send_push_notifications(crn, availability):
    """Send push notifications to all users tracking this CRN"""
    try:
        # Get users tracking this CRN
        users = get_users_tracking_crn(crn)
        
        if not users:
            logger.info(f"No users with push subscriptions found for CRN {crn}")
            return
        
        # Get VAPID keys from secrets
        secrets = get_secrets()
        vapid_private_key = secrets.get('VAPID_PRIVATE_KEY')
        vapid_public_key = secrets.get('VAPID_PUBLIC_KEY')
        
        if not vapid_private_key or not vapid_public_key:
            logger.error('VAPID keys not found in secrets')
            return
        
        # Create notification payload
        course_name = availability.get('course_name', f'CRN {crn}')
        seats_remaining = availability.get('seats_remaining', 0)
        total_seats = availability.get('total_seats', 0)
        
        notification_payload = {
            'title': '🎉 Course Available!',
            'body': f'{course_name} has {seats_remaining}/{total_seats} seats available!',
            'icon': '/logo.png',
            'badge': '/logo.png',
            'data': {
                'crn': crn,
                'course_name': course_name,
                'seats_remaining': seats_remaining,
                'total_seats': total_seats,
                'url': f'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in=202508&crn_in={crn}'
            },
            'tag': f'crn-{crn}',
            'requireInteraction': True,
            'actions': [
                {
                    'action': 'register',
                    'title': 'Register Now',
                    'icon': '/logo.png'
                },
                {
                    'action': 'dismiss',
                    'title': 'Dismiss'
                }
            ]
        }
        
        # Send notifications to all users
        from pywebpush import webpush, WebPushException
        
        successful_sends = 0
        failed_sends = 0
        
        for user in users:
            try:
                response = webpush(
                    subscription_info=user['push_subscription'],
                    data=json.dumps(notification_payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={
                        "sub": "mailto:support@getreaper.com",
                        "aud": user['push_subscription']['endpoint']
                    }
                )
                
                logger.info(f'Successfully sent push notification to user {user["user_id"]} for CRN {crn}')
                successful_sends += 1
                
            except WebPushException as e:
                logger.error(f'WebPush error sending notification to user {user["user_id"]}: {e}')
                failed_sends += 1
            except Exception as e:
                logger.error(f'Error sending notification to user {user["user_id"]}: {e}')
                failed_sends += 1
        
        logger.info(f'Push notification summary for CRN {crn}: {successful_sends} successful, {failed_sends} failed')
        
    except Exception as e:
        logger.error(f"Error sending push notifications: {str(e)}")
        raise 