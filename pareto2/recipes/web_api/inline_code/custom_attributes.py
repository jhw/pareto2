"""
latest info suggests you do *not* use `custom:` prefix when defining in cloudformation, but you *do* need same prefix when referencing from boto3
"""

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cognito-userpool-schemaattribute.html
- A custom attribute value in your user's ID token is always a string, for example "custom:isMember" : "true" or "custom:YearsAsMember" : "12".
"""

"""
This routine might get called by a load of different Cognito Lambda callbacks, because it seems one can never be precisely sure what callback gets called by what action in different sign up / confirm routines (eg Cognito username/password vs social login); hence makes sense to check if a custom attribute exists before blindly writing it
"""

"""
Catching client error on admin_get_user as this is what is thrown if a user doesn't exist; then catching similar for admin_update_user_attributes simply for good measure
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

def handler(event, context):
    user_pool_id = event["userPoolId"]
    username = event["request"]["userAttributes"]["email"]
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    cognito = boto3.client("cognito-idp")
    
    try:
        existing_attributes = {attr["Name"].split(":")[1]: attr["Value"]
                               for attr in cognito.admin_get_user(
                                       UserPoolId=user_pool_id,
                                       Username=username
                               )["UserAttributes"]
                               if attr["Name"].startswith("custom")}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            print(f"User {username} not found: {e}")
        else:
            print(f"An error occurred: {e}")
        return event  # Return the event regardless of the error

    new_attributes = [{'Name': "custom:%s" % attr["name"],
                       'Value': str(attr["value"])}
                      for attr in attributes
                      if attr["name"] not in existing_attributes]

    if new_attributes:
        try:
            cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=new_attributes
            )
        except ClientError as e:
            print(f"An error occurred while updating user attributes: {e}")
            return event  # Return the event even if updating attributes fails    

    return event  # Cognito Lambda triggers must return the event


