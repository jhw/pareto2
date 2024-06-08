import os

def replace_placeholders(message, attributes):
    for key, value in attributes.items():
        message = message.replace(f'{{{key}}}', value)
    return message

def handler(event, context):
    user_attributes = event['request']['userAttributes']
    code_parameter = event['request']['codeParameter']    
    attributes = {**user_attributes, 'codeParameter': code_parameter}    
    if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
        email_subject = os.environ['COGNITO_TEMP_PASSWORD_EMAIL_SUBJECT']
        email_message = os.environ['COGNITO_TEMP_PASSWORD_EMAIL_MESSAGE']
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        email_subject = os.environ['COGNITO_PASSWORD_RESET_EMAIL_SUBJECT']
        email_message = os.environ['COGNITO_PASSWORD_RESET_EMAIL_MESSAGE']
    else:
        return event
    event['response']['emailSubject'] = replace_placeholders(email_subject, attributes)
    event['response']['emailMessage'] = replace_placeholders(email_message, attributes)
    return event
