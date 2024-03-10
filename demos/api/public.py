from pareto2.components.api.public import PublicApi

from pareto2.components import Component

from pareto2.aws.iam import Role

import json, yaml

Endpoints=yaml.safe_load("""
- action: whatevs
  method: GET
  path: hello-get
  parameters:
  - message
- action: whatevs
  method: POST
  path: hello-post
  schema: 
    hello: world
""")

if __name__=="__main__":
    api=PublicApi(namespace="my",
                  endpoints=Endpoints)
    print (json.dumps(api.render(),
                      indent=2))
    print ()
    component=Component()
    role=Role(namespace="backend",
              permissions=["logs:*",
                           "s3:*"])
    component.append(role)
    print (json.dumps(component.render(),
                      indent=2))
    
