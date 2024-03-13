from pareto2.recipes.webapi import WebApi

import json, yaml

Endpoints = yaml.safe_load("""
- method: GET
  path: hello-get
  parameters:
  - message
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
""")

HelloGetBody="""def handler(event, context):
    message=event["queryStringParameters"]["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": f"you sent '{message}' via GET"}"""

HelloPostBody="""import json
def handler(event, context):
    body=json.loads(event["body"])
    message=body["message"]
    return {"statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": f"you sent '{message}' via POST"}"""

if __name__ == "__main__":
    endpoints = {endpoint["path"]:endpoint
                 for endpoint in Endpoints}
    endpoints["hello-get"]["code"] = HelloGetBody
    endpoints["hello-post"]["code"] = HelloPostBody
    api = WebApi(namespace = "my",
                 endpoints = list(endpoints.values()),
                 auth = "private")
    template = api.render()
    template.populate_parameters()
    print (json.dumps(template,
                      indent = 2))
