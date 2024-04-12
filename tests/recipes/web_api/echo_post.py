import base64, json

Headers = {
    "Content-Type": "text/plain",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
    "Access-Control-Allow-Methods": "OPTIONS,POST"
}

def handler(event, context = None, respheaders = Headers):
    try:
        if "headers" not in event:
            raise RuntimeError("request headers not found")
        reqheaders = event["headers"]
        if "origin" not in reqheaders:
            raise RuntimeError("origin not present in request headers")
        respheaders["Access-Control-Allow-Origin"] = reqheaders["origin"]
        if "body" not in event:
            raise RuntimeError("body not found")
        rawbody = event["body"]
        if ("isBase64Encoded" in event and
            event["isBase64Encoded"]):
            rawbody = base64.b64decode(rawbody)
        try:
            reqbody = json.loads(rawbody)
        except:
            raise RuntimeError("couldn't parse JSON request body")
        if not isinstance(reqbody, dict):
            raise RuntimeError("request body must be a dict")
        if not "message" in reqbody:
            raise RuntimeError("message attribute not found")
        message = reqbody["message"]
        if message in ["", None]:
            raise RuntimeError("message attribute can't be blank")
        respbody = f"you sent '{message}' via POST"
        return {"statusCode": 200,
                "headers": respheaders,
                "body": respbody}
    except RuntimeError as error:
        return {"statusCode": 400,
                "headers": respheaders,
                "body": str(error)}

if __name__ == "__main__":
    for headers in [{},
                    {"origin": "http://localhost:3000"}]:
        for event in [{},
                      {"body": json.dumps([])},
                      {"body": json.dumps({"message": "Hello World"})},
                      {"body": base64.b64encode(json.dumps({"message": "Hello World"}).encode("utf-8")),
                       "isBase64Encoded": True},
                      {"body": json.dumps({"message": ""})},                  
                      {"body": json.dumps({"messag": "Hello World"})}]:
            event["headers"] = headers # NB
            resp = handler(event)
            print ("%s\t%s" % (resp["statusCode"], resp["body"]))
            
