from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as APIGWResource
from pareto2.aws.cognito import *
from pareto2.aws.route53 import *

from pareto2.components import Component

import re

class PublicApi(Component):    

    def __init__(self, name, endpoints):
        super().__init__(name=name)
        for klass in [RestApi,
                      Deployment,
                      Stage,
                      GatewayResponse4XX,
                      GatewayResponse5XX,
                      DomainName,
                      BasePathMapping,
                      RecordSet]:
            self.append(klass(name=name))
        for endpoint in endpoints:
            self += self.init_endpoint(endpoint)

    def init_endpoint(self, endpoint):
        name="%s-%s" % (self.name,
                        "-".join([tok.lower()
                                  for tok in re.split("\\W", endpoint["path"])
                                  if tok!=""]))
        resources=[]
        resources.append(APIGWResource(name=name,
                                       path=endpoint["path"]))
        resources.append(CORSMethod(name=name,
                                    method=endpoint["method"]))
        if "parameters" in endpoint:
            resources.append(ParameterRequestValidator(name=name))
            resources.append(PublicLambdaProxyMethod(name=name,
                                                     api_name=self.name,
                                                     function_name="whatevs",
                                                     method=endpoint["method"],
                                                     parameters=endpoint["parameters"]))
        if "schema" in endpoint:
            resources.append(SchemaRequestValidator(name=name))
            resources.append(PublicLambdaProxyMethod(name=name,
                                                     api_name=self.name,
                                                     function_name="whatevs",
                                                     method=endpoint["method"],
                                                     schema=endpoint["schema"]))
            resources.append(Model(name=name,
                                   schema=endpoint["schema"]))
        return resources
            
if __name__=="__main__":
    api=PublicApi(name="hello-api",
                  endpoints=[{"name": "hello-get",
                              "method": "GET",
                              "path": "hello-get",
                              "parameters": ["message"]},
                             {"name": "hello-post",
                              "method": "POST",
                              "path": "hello-post",
                              "schema": {"hello": "world"}}])                             
    import json
    print (json.dumps(api.render(),
                      indent=2))
    
