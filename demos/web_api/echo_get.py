def handler(event, context):
    message=event["queryStringParameters"]["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "OPTIONS,GET"},
            "body": f"you sent '{message}' via GET"}
