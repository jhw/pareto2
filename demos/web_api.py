from pareto2.components.web_api import WebApi

import json, yaml

Endpoints=yaml.safe_load("""
- action: handler
  method: GET
  path: hello-get
  parameters:
  - message
- action: handler
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

if __name__=="__main__":
    api=WebApi(namespace="my",
               endpoints=Endpoints,
               auth="private")
    template=api.render()
    template.populate_parameters()
    print (json.dumps(template,
                      indent=2))

