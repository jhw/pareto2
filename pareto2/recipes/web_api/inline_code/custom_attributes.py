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

import boto3, json, os

def handler(event, context):
    user_pool_id = event["userPoolId"]
    username = event["request"]["userAttributes"]["email"]
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    cognito = boto3.client("cognito-idp")
    existing_attributes = {attr["Name"].split(":")[1]:attr["Value"]
                           for attr in cognito.admin_get_user(
                                   UserPoolId=user_pool_id,
                                   Username=username
                           )["UserAttributes"]
                           if attr["Name"].startswith("custom")}
    new_attributes = [{'Name': "custom:%s" % attr["name"],
                       'Value': str(attr["value"])}
                      for attr in attributes
                      if attr["name"] not in existing_attributes]
    if new_attributes != []:
        cognito.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=new_attributes
        )
    return event # NB Cognito Lambda handlers must return JSON
        

