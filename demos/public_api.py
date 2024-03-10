from pareto2.components.api.public import PublicApi

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
    
