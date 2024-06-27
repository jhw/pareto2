"""
latest info suggests you do *not* use `custom:` prefix when defining in cloudformation, but you *do* need same prefix when referencing from boto3
"""

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cognito-userpool-schemaattribute.html
- A custom attribute value in your user's ID token is always a string, for example "custom:isMember" : "true" or "custom:YearsAsMember" : "12".
"""

import boto3, json, os

def handler(event, context):
    user_pool_id = event["userPoolId"]
    username = event["request"]["userAttributes"]["email"]
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    cognito = boto3.client("cognito-idp")
    for attr in attributes:
        cognito.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {
                    'Name': "custom:%s" % attr["name"],
                    'Value': str(attr["value"])
                }
            ]
        )
    return event # NB Cognito Lambda handlers must return JSON
        

