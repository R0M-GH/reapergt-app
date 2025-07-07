import requests

COMMANDS = [
    {'command': 'help', 'description': 'Show commands'},
    {'command': 'list', 'description': 'List all tracked CRNs'},
    {'command': 'add', 'description': 'Track CRNs: /add 12345'},
    {'command': 'rem', 'description': 'Untrack CRNs: /rem 12345'},
    {'command': 'clear', 'description': 'Clear all tracked CRNs'}
]

url = f'https://api.telegram.org/bot7600978427:AAFeuIb7poqoYaab0wh-Z87z4akV2ryfj0c/setMyCommands'

response = requests.post(url, json={'commands': COMMANDS, "scope": { "type": "default" }})
print(response.status_code)
print(response.json())

url = f'https://api.telegram.org/bot7600978427:AAFeuIb7poqoYaab0wh-Z87z4akV2ryfj0c/getMyCommands'

response = requests.get(url)
print(response.status_code)
print(response.json())