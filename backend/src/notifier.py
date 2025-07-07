import json
import boto3
import asyncio
import aiohttp

def get_secrets():
    """Retrieve secrets from AWS Secrets Manager"""
    try:
        client = boto3.client(service_name='secretsmanager', region_name='us-east-1')
        get_secret_value_response = client.get_secret_value(SecretId='reapergt-secrets-secrets')
        return json.loads(get_secret_value_response['SecretString'])
    except Exception as e:
        print(f'Error getting secrets: {e}')
        raise

secrets = get_secrets()
TELEGRAM_BOT_TOKEN = secrets['TELEGRAM_BOT_TOKEN']

url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

dynamodb = boto3.resource('dynamodb')
crns = dynamodb.Table('reapergt-dynamo-crns')

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            crn = json.loads(record['body'])
            print('Sending notification for CRN: %s' % (crn))
            
            response = crns.get_item(Key={'crn': crn})
            if 'Item' not in response:
                print(f'CRN {crn} not found in database')
                continue
                
            course_info = response['Item']
            course_name = course_info['course_name']
            course_id = course_info['course_id']
            course_section = course_info['course_section']
            user_ids = course_info['user_ids']
            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_notifications(user_ids, crn, course_name, course_id, course_section))
        except json.JSONDecodeError as e:
            print(f'Error decoding CRN from SQS message: {e}')
            continue
        except Exception as e:
            print(f'Error processing CRN {crn}: {e}')
            continue
            
    return {'statusCode': 200, 'body': 'Success'}

async def send_notification(user_id, crn, course_name, course_id, course_section):
    """Send a notification to the user via Telegram"""
    try:
        text = f"⚠️ *COURSE OPEN* ⚠️\n\n*{course_name}*\n{course_id} ({course_section})\n\nCRN: {crn}\n\nRegister [here](https://registration.banner.gatech.edu/StudentRegistrationSsb/ssb/registration/registration)"
        payload = {
            'chat_id': user_id, 
            'text': text, 
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [[
                    {
                        'text': '❌ Unsubscribe',
                        'callback_data': f'unsub_{crn}'
                    }
                ]]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return {'statusCode': 200, 'body': json.dumps({'message': text})}
                else:
                    print(f'Error sending message: {response.status}')
                    return {'statusCode': 500, 'body': 'Error sending message'}
    except Exception as e:
        print(f'Error sending message: {e}')
        return {'statusCode': 500, 'body': 'Error sending message'}

async def send_notifications(user_ids, crn, course_name, course_id, course_section):
    tasks = []
    for user_id in user_ids:
        tasks.append(send_notification(user_id, crn, course_name, course_id, course_section))
    await asyncio.gather(*tasks)
