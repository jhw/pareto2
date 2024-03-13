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

if __name__ == "__main__":
    api = WebApi(namespace = "my",
                 endpoints = Endpoints,
                 auth = "private")
    template = api.render()
    template.populate_parameters()
    print (json.dumps(template,
                      indent = 2))

