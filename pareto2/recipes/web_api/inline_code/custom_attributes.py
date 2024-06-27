import boto3, json, os

def format_value(type, value):
    if type == "int":
        return int(value)
    elif type == "bool":
        return bool(value)
    else:
        return str(value)

"""
latest info suggests you do *not* use `custom:` prefix when defining in cloudformation, but you *do* need same prefix when referencing from boto3
"""
    
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
                    'Value': format_value(attr["type"], attr["value"])
                }
            ]
        )
    return event # NB Cognito Lambda handlers must return JSON
        

