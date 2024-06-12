import os

def replace_placeholders(message, template_values):
    for key, value in template_values.items():
        message = message.replace(f'{{{key}}}', value)
    return message

def validate_placeholders(message, required_placeholders):
    for placeholder in required_placeholders:
        if f'{{{placeholder}}}' not in message:
            raise RuntimeError(f"Missing required placeholder: {{{placeholder}}}")

"""
Commenting out username override as -

Error: An error occurred (InvalidLambdaResponseException) when calling the AdminCreateUser operation: Invalid user name. User name in Lambda mismatches the actual username.
"""
        
def handler(event, context):
    # event['userName'] = event['request']['userAttributes']['email']
    template_values = {'username': event['request']['usernameParameter'],
                       'code': event['request']['codeParameter']}
    if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
        email_subject = os.environ['TEMP_PASSWORD_EMAIL_SUBJECT']
        email_message = os.environ['TEMP_PASSWORD_EMAIL_MESSAGE']
        required_placeholders = ['username', 'code']
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        email_subject = os.environ['PASSWORD_RESET_EMAIL_SUBJECT']
        email_message = os.environ['PASSWORD_RESET_EMAIL_MESSAGE']
        required_placeholders = ['code']
    else:
        return event
    validate_placeholders(email_message, required_placeholders)
    event['response']['emailSubject'] = replace_placeholders(email_subject, template_values)
    event['response']['emailMessage'] = replace_placeholders(email_message, template_values)
    return event
