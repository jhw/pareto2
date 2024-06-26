import boto3, json, os

def handler(event, context):
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    for attr in attributes:
        print (attr)
        

