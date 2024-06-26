import boto3, json, os

def handler(event, context):
    user_pool_id = event["userPoolId"]
    print (user_pool_id)
    username = event["request"]["userAttributes"]["email"]
    print (username)
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    cognito = boto3.client("cognito-idp")
    for attr in attributes:
        print (attr)
        

