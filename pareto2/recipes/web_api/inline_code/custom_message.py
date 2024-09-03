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
        message = message.replace(f'{{{key}}}', value)
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
    template_values = {attr: event['request'][f"{attr}Parameter"]
                       for attr in ["username", "code"]
                       if f"{attr}Parameter" in event["request"]}
    event['response']['emailSubject'] = replace_placeholders(subject_body, template_values)
    event['response']['emailMessage'] = replace_placeholders(message_body, template_values)
    return event # NB Cognito Lambda handlers must return JSON

