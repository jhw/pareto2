from pareto2.recipes.webapi import WebApi

import json, yaml

Endpoints = yaml.safe_load("""
- action: echo
  method: GET
  path: hello-get
  parameters:
  - message
- action: echo
  method: POST
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

SampleCodeBody="""def handler(event, context):
    print (event)"""

if __name__ == "__main__":
    endpoints = {endpoint["path"]:endpoint
                 for endpoint in Endpoints}
    endpoints["hello-get"]["code"] = SampleCodeBody
    endpoints["hello-post"]["code"] = SampleCodeBody
    api = WebApi(namespace = "my",
                 endpoints = list(endpoints.values()),
                 auth = "private")
    template = api.render()
    template.populate_parameters()
    print (json.dumps(template,
                      indent = 2))

