import json

def handler(event, context):
    body=json.loads(event["body"])
    message=body["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "OPTIONS,POST"},
            "body": f"you sent '{message}' via POST"}
