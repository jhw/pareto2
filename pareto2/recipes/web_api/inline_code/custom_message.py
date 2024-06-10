import os

def replace_placeholders(message, attributes):
    for key, value in attributes.items():
        message = message.replace(f'{{{key}}}', value)
    return message

def validate_placeholders(message, required_placeholders):
    for placeholder in required_placeholders:
        if f'{{{placeholder}}}' not in message:
            raise RuntimeError(f"Missing required placeholder: {{{placeholder}}}")

"""
Yes, that's correct. The custom message for the AdminCreateUser trigger requires a username placeholder (lower case) in the email message template, while the event structure provides this value in a userName (camel case) key.
"""
        
def handler(event, context):
    user_attributes = event['request']['userAttributes']
    code_parameter = event['request']['codeParameter']
    user_name = event['userName']
    attributes = {**user_attributes, 'codeParameter': code_parameter, 'username': user_name}    
    if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
        email_subject = os.environ['TEMP_PASSWORD_EMAIL_SUBJECT']
        email_message = os.environ['TEMP_PASSWORD_EMAIL_MESSAGE']
        required_placeholders = ['username', 'codeParameter']
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        email_subject = os.environ['PASSWORD_RESET_EMAIL_SUBJECT']
        email_message = os.environ['PASSWORD_RESET_EMAIL_MESSAGE']
        required_placeholders = ['codeParameter']
    else:
        return event
    validate_placeholders(email_message, required_placeholders)
    event['response']['emailSubject'] = replace_placeholders(email_subject, attributes)
    event['response']['emailMessage'] = replace_placeholders(email_message, attributes)    
    return event
