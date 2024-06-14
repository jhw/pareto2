"""
This stuff is the biggest nightmare ever
AdminCreateUser requires username and code parameters
But these are the names of the parameters at the pareto2 api level, for convenience
Cognito requires different placeholders, as defined in request.usernameParameter and request.codeParameter (there is also request.linkParameter)
And these differ from the pareto2 api placeholder names; in particular codeParameter is typically {####} not {code} (but {username} is {username})
The handlers job is to insert these placeholders into the message, not the pareto2 api placeholders
And not also you do not paste *values* into the template; you are inserting Cognito- compliant placeholders
Cognito will then insert values for the placeholders into the template, after the handler has run
---
Assuming this is done correctly, there's then the question of where the values come from
I have no idea where code comes from, nor link
username comes from event.userName
But this doesn't always seem to be in username form, in fact mine look more like a UUID
You can't seem to override this with an email address, if it is not an email address by default
There are links on the web which say you should also urlquote the username value, which I think are incorrect
Instead you have to make sure that your UserPool is configured to use email as user id
And this seems to mean defining not just UsernameAttributes: email, but also UsernameConfiguration as well; without the latter, it seems userName is not guaranteed to be an email
It's important to have logging enabled to you can see what messages Cognito is actually sending into the handler here
---

If a message body isn't well formed then it will simply be silently ignored by Cognito
No message is generated, so it's impossible to figure out why your custom message isn't being used; you will simply see the default message instead
"""

import logging, os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def replace_placeholders(message, template_values):
    for key, value in template_values.items():
        message = message.replace(f'{{{key}}}', value)
    return message

def validate_placeholders(message, required_placeholders):
    for placeholder in required_placeholders:
        if f'{{{placeholder}}}' not in message:
            raise RuntimeError(f"Missing required placeholder: {{{placeholder}}}")

"""
"""
        
def handler(event, context):
    logger.info("Event [START]: %s", event)
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
    logger.info("Event [END]: %s", event)
    return event
