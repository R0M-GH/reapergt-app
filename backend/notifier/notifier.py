import json
import boto3
import os
import logging
import requests
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')

def handler(event, context):
    """
    Notifier Lambda function
    Triggered directly by scraper Lambda
    Sends Telegram notifications when course spots are available
    """
    try:
        logger.info("Notifier started")
        logger.info(f"Processing notification: {event}")
        
        # Get Telegram bot token from secrets
        telegram_token = get_telegram_token()
        
        # Process the direct invocation event
        if event.get('notification_type') == 'course_available':
            crn = event.get('crn')
            availability = event.get('availability')
            
            # Send Telegram notification
            send_telegram_notification(telegram_token, crn, availability)
            logger.info(f"Telegram notification sent for CRN {crn}")
        
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

def get_telegram_token():
    """Get Telegram bot token from AWS Secrets Manager"""
    try:
        secret_name = "reaper-secrets"
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        return secrets['TELEGRAM_BOT_TOKEN']
    except Exception as e:
        logger.error(f"Error getting Telegram token: {str(e)}")
        raise

def send_telegram_notification(token, crn, availability):
    """Send notification via Telegram"""
    try:
        # This would be replaced with actual Telegram chat IDs
        # For now, we'll just log the notification
        message = f"🎉 Course Available!\n\n"
        message += f"CRN: {crn}\n"
        message += f"Spots Available: {availability.get('spots_available', 0)}\n"
        message += f"Total Spots: {availability.get('total_spots', 0)}\n"
        message += f"Checked: {availability.get('last_checked', 'Unknown')}\n\n"
        message += f"Register now before spots fill up!"
        
        # Placeholder for actual Telegram API call
        # telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
        # payload = {
        #     'chat_id': CHAT_ID,  # Would get from user preferences
        #     'text': message,
        #     'parse_mode': 'HTML'
        # }
        # response = requests.post(telegram_url, json=payload)
        
        logger.info(f"Telegram notification prepared: {message}")
        
        # For now, just log the message since we don't have actual chat IDs
        logger.info("Telegram notification would be sent here")
        
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        raise

def get_user_chat_ids_for_crn(crn):
    """Get list of Telegram chat IDs for users tracking this CRN"""
    try:
        # This would query DynamoDB to find users tracking this CRN
        # and return their Telegram chat IDs
        return []  # Placeholder
    except Exception as e:
        logger.error(f"Error getting chat IDs for CRN {crn}: {str(e)}")
        return [] 