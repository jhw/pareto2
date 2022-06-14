import json

def handler(event, context=None):
    reqbody=json.loads(event["body"])
    message=reqbody["message"]
    respbody={"message": "you sent: '%s'" % message}
    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(respbody)}

