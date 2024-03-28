Headers = {
    "Content-Type": "text/plain",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
    "Access-Control-Allow-Methods": "OPTIONS,GET"
}

def handler(event, context = None, headers = Headers):
    try:
        if "queryStringParameters" not in event:
            raise RuntimeError("querystring not found")
        qs = event["queryStringParameters"]
        if "message" not in qs:
            raise RuntimeError("message parameter not found")
        message = qs["message"]
        if message in ["", None]:
            raise RuntimeError("message parameter can't be blank")
        respbody = f"you sent '{message}' via GET"       
        return {"statusCode": 200,
                "headers": headers,
                "body": respbody}
    except RuntimeError as error:
        return {"statusCode": 400,
                "headers": headers,
                "body": str(error)}

if __name__ == "__main__":
    for event in [{},
                  {"queryStringParameters": {"message": "Hello World"}},
                  {"queryStringParameters": {"message": ""}},
                  {"queryStringParameters": {"messag": "Hello World"}}]:
        resp = handler(event)
        print ("%s\t%s" % (resp["statusCode"], resp["body"]))

