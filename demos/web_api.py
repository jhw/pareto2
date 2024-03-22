from pareto2.recipes.web_api import WebApi

import json, os, yaml

Endpoints = yaml.safe_load("""
- method: GET
  path: hello-get
  parameters:
  - message
  permissions:
  - s3:GetObject
- method: POST
  path: hello-post
  schema: 
    type: object
    properties: 
      message:
        type: string
    required:
    - message
    additionalProperties: false
  permissions:
  - s3:GetObject
  - s3:PutObject
""")

HelloGetBody="""def handler(event, context):
    message=event["queryStringParameters"]["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
                        "Access-Control-Allow-Methods": "OPTIONS,GET"},
            "body": f"you sent '{message}' via GET"}"""

HelloPostBody="""import json
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
    endpoints = {endpoint["path"]:endpoint
                 for endpoint in Endpoints}
    endpoints["hello-get"]["code"] = HelloGetBody
    endpoints["hello-post"]["code"] = HelloPostBody
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    for auth in ["public",
                 "private"]:
        template = WebApi(namespace = "app",
                          endpoints = list(endpoints.values()),
                          auth = auth).render()
        template.populate_parameters()
        with open(f"tmp/web-api-{auth}.json", 'w') as f:
            f.write(json.dumps(template,
                               sort_keys = True,
                               indent = 2))
        print ("%s: %s" % (auth, ", ".join(list(template["Parameters"].keys()))))
