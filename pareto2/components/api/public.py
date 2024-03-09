from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as APIGWResource
from pareto2.aws.cognito import *
from pareto2.aws.route53 import *

from pareto2.components import Component

import re

class PublicApi(Component):    

    def __init__(self, namespace, endpoints):
        super().__init__(namespace=namespace)
        self += self.init_api()
        for endpoint in endpoints:
            self += self.init_endpoint(endpoint)

    def init_api(self):
        return [klass(namespace=self.namespace)
                for klass in [RestApi,
                              Deployment,
                              Stage,
                              GatewayResponse4XX,
                              GatewayResponse5XX,
                              DomainName,
                              BasePathMapping,
                              RecordSet]]
            
    def init_endpoint(self, endpoint):
        namespace="%s-%s" % (self.namespace,
                        "-".join([tok.lower()
                                  for tok in re.split("\\W", endpoint["path"])
                                  if tok!=""]))
        resources=[]
        resources.append(APIGWResource(namespace=namespace,
                                       path=endpoint["path"]))
        resources.append(CORSMethod(namespace=namespace,
                                    method=endpoint["method"]))
        if "parameters" in endpoint:
            resources.append(ParameterRequestValidator(namespace=namespace))
            resources.append(PublicLambdaProxyMethod(namespace=namespace,
                                                     api_namespace=self.namespace,
                                                     function_namespace="whatevs",
                                                     method=endpoint["method"],
                                                     parameters=endpoint["parameters"]))
        if "schema" in endpoint:
            resources.append(SchemaRequestValidator(namespace=namespace))
            resources.append(PublicLambdaProxyMethod(namespace=namespace,
                                                     api_namespace=self.namespace,
                                                     function_namespace="whatevs",
                                                     method=endpoint["method"],
                                                     schema=endpoint["schema"]))
            resources.append(Model(namespace=namespace,
                                   schema=endpoint["schema"]))
        return resources
            
if __name__=="__main__":
    api=PublicApi(namespace="hello-api",
                  endpoints=[{"method": "GET",
                              "path": "hello-get",
                              "parameters": ["message"]},
                             {"method": "POST",
                              "path": "hello-post",
                              "schema": {"hello": "world"}}])                             
    import json
    print (json.dumps(api.render(),
                      indent=2))
    
