from pareto2.recipes.web_api import WebApi

import json, os, yaml

Endpoints = yaml.safe_load("""
- method: GET
  path: public-get
  auth: public
  parameters:
  - message
  permissions:
  - s3:GetObject
- method: POST
  path: public-post
  auth: public
  permissions:
  - s3:GetObject
  - s3:PutObject
- method: GET
  path: private-get
  auth: private
  parameters:
  - message
  permissions:
  - s3:GetObject
- method: POST
  path: private-post
  auth: private
  permissions:
  - s3:GetObject
  - s3:PutObject
""")

EchoGetBody="""def handler(event, context):
    message=event["queryStringParameters"]["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "OPTIONS,GET"},
            "body": f"you sent '{message}' via GET"}"""

EchoPostBody="""import json
def handler(event, context):
    body=json.loads(event["body"])
    message=body["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "OPTIONS,POST"},
            "body": f"you sent '{message}' via POST"}"""

if __name__ == "__main__":
    try:
        endpoints = {endpoint["path"]:endpoint
                     for endpoint in Endpoints}
        for path, endpoint in endpoints.items():
            if "get" in path:
                endpoint["code"] = EchoGetBody
            elif "post" in path:
                endpoint["code"] = EchoPostBody
            else:
                raise RuntimeError("couldn't embed code body for endpoint %s" % path)
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        template = WebApi(namespace = "app",
                          endpoints = list(endpoints.values())).render()
        template.populate_parameters()
        with open(f"tmp/web-api.json", 'w') as f:
            f.write(json.dumps(template,
                               sort_keys = True,
                               indent = 2))
        print (", ".join(list(template["Parameters"].keys())))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
