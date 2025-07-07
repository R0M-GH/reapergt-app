import json
import urllib.request
import boto3
import re
from typing import Union, List, Tuple

def get_secrets():
    """Retrieve secrets from AWS Secrets Manager.
    
    Returns:
        dict: The secrets containing TELEGRAM_BOT_TOKEN and TERM_CODE.
        
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
TELEGRAM_BOT_TOKEN = secrets['TELEGRAM_BOT_TOKEN']
TERM = secrets['TERM_CODE']

url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/'
ENDPOINT = 'https://oscar.gatech.edu/pls/bprod/bwckschd.p_disp_detail_sched?term_in=%s&crn_in=%s'

COMMANDS = [
    {'command': '/help', 'description': 'Show all commands\' descriptions'},
    {'command': '/list', 'description': 'List all class CRNs being tracked with details'},
    {'command': '/add', 'description': 'Add CRN(s) to the tracker. (e.g., /add 12345, 67890)'},
    {'command': '/rem', 'description': 'Remove CRN(s) from the tracker. (e.g., /rem 12345, 67890)'},
    {'command': '/clear', 'description': 'Remove all tracked CRNs'}
]

MAX_CRNS_PER_USER = 5

dyamodb = boto3.resource('dynamodb')
crns = dyamodb.Table('reapergt-dynamo-crns')
users = dyamodb.Table('reapergt-dynamo-users')

_NAME_RE = re.compile(r'<th[^>]*class=["\']ddlabel["\'][^>]*>(.*?)</th>', re.IGNORECASE | re.DOTALL)

def lambda_handler(event, context):
    """Handle incoming Telegram bot commands.
    
    Args:
        event (dict): The Lambda event containing the Telegram message.
        context (object): The Lambda context.
        
    Returns:
        dict: Response with status code and body.
    """
    try:
        body = json.loads(event['body'])
        print(body)
        
        if 'callback_query' in body:
            handle_callback(body['callback_query'])
            return {'statusCode': 200, 'body': 'Callback handled.'}
        
        if 'message' in body and 'entities' in body['message'] and body['message']['entities'][0]['type'] == 'bot_command':
            user_id = str(body['message']['chat']['id'])
            message = body['message']['text']
            text = handle_command(message, user_id)
            return send_message(user_id, text)
        
        return {'statusCode': 200, 'body': 'Invalid request format.'}
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {'statusCode': 500, 'body': 'Internal server error'}

def handle_command(message, user_id):
    try:
        breakdown = message.split(' ', 1)
        command = breakdown[0].strip()
        args = breakdown[1].strip() if len(breakdown) > 1 else ''
        
        valid_commands = [cmd['command'] for cmd in COMMANDS]
        if command not in valid_commands:
            return f"❌ Unknown command: {command}\n\nUse /help to see available commands."
        
        if command == '/clear':
            tracked_crns = get_tracked_crns(user_id)
            if not tracked_crns:
                return "ℹ️ You don't have any CRNs to clear."
            
            cleared = []
            failed = []
            
            for crn in tracked_crns:
                response = unsubscribe_from_crn(crn, user_id)
                if response == f"You are no longer tracking {crn}.":
                    cleared.append(crn)
                else:
                    failed.append(crn)
            
            message_parts = []
            if cleared:
                message_parts.append(f"✅ Cleared {len(cleared)} CRN{'s' if len(cleared) != 1 else ''}: {', '.join(cleared)}")
            if failed:
                message_parts.append(f"❌ Failed to clear {len(failed)} CRNs: {', '.join(failed)}")
            
            return "\n".join(message_parts)
        
        elif command == '/add':
            if not args:
                return "❌ Please provide at least one CRN to add.\n\n*Format:* `/add 12345, 67890`"
            
            crns_to_add = []
            for part in args.replace(',', ' ').split():
                crn = part.strip()
                if crn:
                    crns_to_add.append(crn)
            
            if not crns_to_add:
                return "❌ No valid CRNs provided.\n\n*Format:* `/add 12345, 67890`"
            
            invalid_crns = []
            valid_crns = []
            
            for crn in crns_to_add:
                is_valid, error_msg = validate_crn(crn)
                if not is_valid:
                    invalid_crns.append(f"{crn} ({error_msg})")
                else:
                    valid_crns.append(crn)
            
            if not valid_crns:
                return f"❌ Invalid CRNs:\n• " + "\n• ".join(invalid_crns)
            
            current_crns = get_tracked_crns(user_id)
            if len(current_crns) + len(valid_crns) > MAX_CRNS_PER_USER:
                return f"❌ You can only track up to {MAX_CRNS_PER_USER} CRNs. You currently have {len(current_crns)} tracked."
            
            added = []
            already_tracking = []
            failed = []
            
            for crn in valid_crns:
                if crn in current_crns:
                    already_tracking.append(crn)
                    continue
                    
                response = subscribe_to_crn(crn, user_id)
                if response:
                    added.append(crn)
                else:
                    failed.append(crn)
            
            message_parts = []
            if added:
                message_parts.append(f"✅ Added: {', '.join(added)}")
            if already_tracking:
                message_parts.append(f"ℹ️ Already tracking: {', '.join(already_tracking)}")
            if failed:
                message_parts.append(f"❌ Failed to add: {', '.join(failed)}")
            if invalid_crns:
                message_parts.append(f"❌ Invalid CRNs:\n• " + "\n• ".join(invalid_crns))
            
            return "\n".join(message_parts) if message_parts else "ℹ️ No CRNs were added."
        
        elif command == '/rem':
            if not args:
                return "❌ Please provide at least one CRN to remove.\n\n*Format:* `/rem 12345, 67890`"
            
            crns_to_remove = []
            for part in args.replace(',', ' ').split():
                crn = part.strip()
                if crn:
                    crns_to_remove.append(crn)
            
            if not crns_to_remove:
                return "❌ No valid CRNs provided.\n\n*Format:* `/rem 12345, 67890`"
            
            invalid_crns = []
            valid_crns = []
            
            for crn in crns_to_remove:
                is_valid, error_msg = validate_crn(crn)
                if not is_valid:
                    invalid_crns.append(f"{crn} ({error_msg})")
            
            if invalid_crns:
                return f"❌ Invalid CRNs:\n• " + "\n• ".join(invalid_crns)
            
            removed = []
            not_tracking = []
            failed = []
            
            for crn in crns_to_remove:
                response = unsubscribe_from_crn(crn, user_id)
                if response == f"You are no longer tracking {crn}.":
                    removed.append(crn)
                elif response == f"You are not currently tracking {crn}.":
                    not_tracking.append(crn)
                else:
                    failed.append(crn)
            
            message_parts = []
            if removed:
                message_parts.append(f"✅ Removed: {', '.join(removed)}")
            if not_tracking:
                message_parts.append(f"ℹ️ Not tracking: {', '.join(not_tracking)}")
            if failed:
                message_parts.append(f"❌ Failed to remove: {', '.join(failed)}")
            
            return "\n".join(message_parts) if message_parts else "ℹ️ No CRNs were removed."
        
        elif command == '/list':
            tracked_crns = get_tracked_crns(user_id)
            if not tracked_crns:
                return "📋 *Your Tracked Courses*\n\n_No courses are currently being tracked._\n\nUse `/add` to start tracking courses!"
            
            course_list = []
            for crn in tracked_crns:
                try:
                    response = crns.get_item(Key={'crn': crn})
                    if 'Item' in response:
                        item = response['Item']
                        course_name = item.get('course_name', 'N/A')
                        course_id = item.get('course_id', 'N/A')
                        course_section = item.get('course_section', 'N/A')
                        course_list.append(f"• `{crn}` - _{course_name} ({course_id} {course_section})_")
                    else:
                        course_list.append(f"• `{crn}` - _Course info pending_")
                except Exception as e:
                    print(f"Error fetching course info for {crn}: {e}")
                    course_list.append(f"• `{crn}` - _Error fetching info_")
            
            return f"📋 *Your Tracked Courses* ({len(tracked_crns)}/{MAX_CRNS_PER_USER})\n\n" + "\n".join(course_list)
        
        elif command == '/help':
            help_message = "🤖 *Available Commands:*\n\n"
            for cmd in COMMANDS:
                help_message += f"• `{cmd['command']}` - _{cmd['description']}_\n"
            help_message += f"\n_Limits:_\n• Max {MAX_CRNS_PER_USER} tracked courses"
            help_message += "\n\nNeed help? Have suggestions? Contact us on Instagram [@reaper_gt](https://instagram.com/reaper_gt)"
            return help_message
    except Exception as e:
        print(f"Error in handle_command: {e}")
        return "❌ An error occurred while processing your command. Please try again."

def handle_callback(callback_query):
    """Handle Telegram callback queries (e.g., unsubscribe button)"""
    try:
        callback_id = callback_query['id']
        user_id = str(callback_query['from']['id'])
        data = callback_query['data']

        if data.startswith('unsub_'):
            crn = data[len('unsub_'):]
            result = unsubscribe_from_crn(crn, user_id)
            send_message(user_id, result or f"❌ Failed to unsubscribe from {crn}.")
            answer_callback(callback_id, text="Unsubscribed!" if result else "Failed to unsubscribe.")
    except Exception as e:
        print(f"Error handling callback: {e}")

def answer_callback(callback_id, text=""):
    """Answer a Telegram callback query to remove the loading spinner"""
    try:
        answer_url = url + 'answerCallbackQuery'
        payload = {'callback_query_id': callback_id, 'text': text, 'show_alert': False}
        data = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(answer_url, data=data, headers=headers)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error answering callback: {e}")

def subscribe_to_crn(crn, user_id):
    """Subscribe the user to a CRN and send confirmation message"""
    try:
        crns.update_item(
            Key={'crn': crn},
            UpdateExpression='ADD user_ids :new_user SET course_info = if_not_exists(course_info, :null), course_name = if_not_exists(course_name, :null), course_id = if_not_exists(course_id, :null), course_section = if_not_exists(course_section, :null)',
            ExpressionAttributeValues={
                ':new_user': {user_id},
                ':null': None
            }
        )
        
        users.update_item(
            Key={'user_id': user_id},
            UpdateExpression='ADD crns :new_crn',
            ExpressionAttributeValues={
                ':new_crn': {crn}
            }
        )
        return f'You are now tracking {crn}.'
    except Exception as e:
        print(f'Error subscribing to CRN: {e}')
        return None

def unsubscribe_from_crn(crn, user_id):
    """Unsubscribe the user from a CRN and send confirmation message"""
    try:
        user_response = users.get_item(Key={'user_id': user_id})
        user_crns = user_response.get('Item', {}).get('crns', set())
        
        if crn not in user_crns:
            return f"You are not currently tracking {crn}."
        
        crns.update_item(
            Key={'crn': crn},
            UpdateExpression='DELETE user_ids :user',
            ExpressionAttributeValues={
                ':user': {user_id}
            },
            ReturnValues='ALL_NEW'
        )
        
        response = crns.get_item(Key={'crn': crn})
        if 'Item' not in response or 'user_ids' not in response['Item'] or response['Item']['user_ids'] == set():
            crns.delete_item(Key={'crn': crn})
        
        users.update_item(
            Key={'user_id': user_id},
            UpdateExpression='DELETE crns :crn',
            ExpressionAttributeValues={
                ':crn': {crn}
            },
            ReturnValues='ALL_NEW'
        )
        
        response = users.get_item(Key={'user_id': user_id})
        if response.get('Item', {}).get('crns', set()) == set():
            users.delete_item(Key={'user_id': user_id})
        
        return f'You are no longer tracking {crn}.'
    except Exception as e:
        print(f'Error unsubscribing from CRN: {e}')
        return None

def get_tracked_crns(user_id):
    """Get the list of CRNs the user is tracking"""
    try:
        response = users.get_item(Key={'user_id': user_id})
        return response.get('Item', {}).get('crns', set())
    except Exception as e:
        print(f'Error getting tracked CRNs: {e}')
        return set()

def send_message(user_id, text):
    """Send a message to the user via Telegram"""
    try:
        payload = {'chat_id': user_id, 'text': text, 'parse_mode': 'Markdown'}
        data = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url + 'sendMessage', data=data, headers=headers)
        urllib.request.urlopen(req)
        
        return {'statusCode': 200, 'body': json.dumps({'message': text})}
    except Exception as e:
        print(f'Error sending message: {e}')
        return {'statusCode': 500, 'body': 'Error sending message'}

def validate_crn(crn):
    """Validate a CRN number by checking both format and existence in the course system.
    If valid, also parses and stores course information in DynamoDB.
    
    Args:
        crn (str): The CRN to validate.
        
    Returns:
        tuple[bool, str]: (is_valid, error_message) where error_message is empty if valid.
    """
    if not crn.isdigit() or len(crn) != 5:
        return False, "CRN must be a 5-digit number"
    
    try:
        url = ENDPOINT % (TERM, crn)
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
            if _NAME_RE.search(html) is None:
                return False, "CRN does not exist"
            
            name_match = _NAME_RE.search(html)
            if name_match:
                name = [part.strip().replace('<br />', '').replace('<br>', '') for part in name_match.group(1).split(" - ")]
                
                if len(name) >= 4:
                    # Parse seat data to determine if course is open
                    import re
                    _TABLE_RE = re.compile(r'<table[^>]*summary=["\']This layout table is used to present the seating numbers\.["\'][^>]*>(.*?)</table>', re.IGNORECASE | re.DOTALL)
                    _TD_RE = re.compile(r'<td[^>]*class=["\']dddefault["\'][^>]*>([^<]+)</td>', re.IGNORECASE)
                    
                    m_table = _TABLE_RE.search(html)
                    isOpen = False
                    if m_table:
                        snippet = m_table.group(1)
                        data = _TD_RE.findall(snippet)
                        if len(data) >= 3 and int(data[2]) > 0:
                            isOpen = True
                    
                    crns.update_item(
                        Key={'crn': crn},
                        UpdateExpression='SET course_name = :course_name, course_id = :course_id, course_section = :course_section, isOpen = :isOpen',
                        ExpressionAttributeValues={
                            ':course_name': name[0],
                            ':course_id': name[2],
                            ':course_section': name[3],
                            ':isOpen': isOpen
                        }
                    )
            
            return True, ""
    except Exception as e:
        print(f'Error validating CRN {crn}: {e}')
        return False, "Error checking CRN"
