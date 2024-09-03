"""
https://stackoverflow.com/a/78622562/124179
"""

"""
if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
    required_placeholders = ['username', 'code']
elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
    required_placeholders = ['code']
"""

import json
import os

def replace_placeholders(message, template_values):
    for key, value in template_values.items():
        # Use an empty string if the value is None
        message = message.replace(f'{{{key}}}', value if value is not None else '')
    return message

def handler(event, context):
    templates = json.loads(os.environ["EMAIL_TEMPLATES"])
    
    if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
        subject_body = templates["temp_password"]["subject"]
        message_body = templates["temp_password"]["message"]
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        subject_body = templates["password_reset"]["subject"]
        message_body = templates["password_reset"]["message"]
    else:
        return event
    
    # Safely get the parameters, defaulting to an empty string if not present
    template_values = {
        "username": event['request'].get('usernameParameter', ''),
        "code": event['request'].get('codeParameter', '')
    }
    
    event['response']['emailSubject'] = replace_placeholders(subject_body, template_values)
    event['response']['emailMessage'] = replace_placeholders(message_body, template_values)
    
    return event  # Cognito Lambda handlers must return JSON


