import json
import boto3
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sqs = boto3.client('sqs')

def handler(event, context):
    """
    Dispatcher Lambda function
    Triggered by EventBridge scheduler every minute
    Sends scraping tasks to the scraper queue
    """
    try:
        logger.info("Dispatcher started")
        
        # Get queue URL from environment
        queue_url = os.environ.get('SCRAPERQUEUE_QUEUE_URL')
        if not queue_url:
            raise ValueError("SCRAPERQUEUE_QUEUE_URL environment variable not set")
        
        # Create scraping task message with high-frequency flag
        message = {
            'task_type': 'scrape_courses',
            'timestamp': datetime.utcnow().isoformat(),
            'triggered_by': 'scheduler',
            'frequency': 'high',  # Indicates 10-second intervals
            'priority': 'real-time'
        }
        
        # Send message to scraper queue
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'TaskType': {
                    'StringValue': 'scrape_courses',
                    'DataType': 'String'
                }
            }
        )
        
        logger.info(f"Successfully sent scraping task to queue. MessageId: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Scraping task dispatched successfully',
                'messageId': response['MessageId'],
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in dispatcher: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to dispatch scraping task',
                'details': str(e)
            })
        } 