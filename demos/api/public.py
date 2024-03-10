from pareto2.components.api.public import PublicApi

from pareto2.aws.iam import Role

import json

if __name__=="__main__":
    api=PublicApi(namespace="my",
                  endpoints=[{"action": "whatevs",
                              "method": "GET",
                              "path": "hello-get",
                              "parameters": ["message"]},
                             {"action": "whatevs",
                              "method": "POST",
                              "path": "hello-post",
                              "schema": {"hello": "world"}}])
    role=Role(namespace="foobar",
              permissions=["logs:*",
                           "s3:*"])
    api.append(role)
    print (json.dumps(api.render(),
                      indent=2))
    
    
