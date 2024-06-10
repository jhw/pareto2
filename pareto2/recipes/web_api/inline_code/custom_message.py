import logging, os, urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def replace_placeholders(message, attributes):
    for key, value in attributes.items():
        message = message.replace(f'{{{key}}}', value)
    return message

def validate_placeholders(message, required_placeholders):
    for placeholder in required_placeholders:
        if f'{{{placeholder}}}' not in message:
            raise RuntimeError(f"Missing required placeholder: {{{placeholder}}}")

"""
https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-custom-message.html#cognito-user-pools-lambda-trigger-syntax-custom-message
https://github.com/aws-amplify/amplify-js/issues/2487#issuecomment-535902638
""" 

"""
Yes, you are correct. The {####} placeholder in the codeParameter is used by Amazon Cognito to be replaced with the actual temporary password or verification code later when the email is sent. The Lambda function only sees the placeholder {####} and does not have access to the actual code.
"""

def handler(event, context):
    # START TEMP CODE
    logger.info("Event [START]: %s", event)
    # END TEMP CODE
    user_attributes = event['request']['userAttributes']
    code_parameter = event['request']['codeParameter']
    user_name = event['request']['userAttributes']['email']
    username_parameter = urllib.parse.quote(user_name)  # URL-encode the usernameParameter
    attributes = {**user_attributes,
                  'codeParameter': code_parameter,
                  'usernameParameter': username_parameter}
    if event['triggerSource'] == 'CustomMessage_AdminCreateUser':
        email_subject = os.environ['TEMP_PASSWORD_EMAIL_SUBJECT']
        email_message = os.environ['TEMP_PASSWORD_EMAIL_MESSAGE']
        required_placeholders = ['usernameParameter',
                                 'codeParameter']
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        email_subject = os.environ['PASSWORD_RESET_EMAIL_SUBJECT']
        email_message = os.environ['PASSWORD_RESET_EMAIL_MESSAGE']
        required_placeholders = ['codeParameter']
    else:
        return event
    validate_placeholders(email_message, required_placeholders)
    event['response']['emailSubject'] = replace_placeholders(email_subject, attributes)
    event['response']['emailMessage'] = replace_placeholders(email_message, attributes)
    # START TEMP CODE
    logger.info("Event [END]: %s", event)
    # END TEMP CODE
    return event
