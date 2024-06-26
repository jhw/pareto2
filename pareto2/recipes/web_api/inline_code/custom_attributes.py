import boto3, json, os

def handler(event, context):
    cognito = boto3.client("cognito-idp")
    username = event["request"]["userAttributes"]["email"]
    print (username)
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    for attr in attributes:
        print (attr)
        

