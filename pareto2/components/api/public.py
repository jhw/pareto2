from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as APIGWResource
from pareto2.aws.cognito import *
from pareto2.aws.route53 import *

from pareto2.components import Component

from pareto2.components.api import Permission

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
        parent_ns = self.namespace
        child_ns ="%s-%s" % (parent_ns,
                             "-".join([tok.lower()
                                       for tok in re.split("\\W", endpoint["path"])
                                       if tok != ""]))
        resources=[]
        resources.append(APIGWResource(namespace=child_ns,
                                       api_namespace=parent_ns,
                                       path=endpoint["path"]))
        resources.append(CORSMethod(namespace=child_ns,
                                    api_namespace=parent_ns,
                                    method=endpoint["method"]))
        resources.append(Permission(namespace=child_ns,
                                    api_namespace=parent_ns,
                                    function_namespace=endpoint["action"],
                                    method=endpoint["method"],
                                    path=endpoint["path"]))                                    
        if "parameters" in endpoint:
            resources.append(ParameterRequestValidator(namespace=child_ns,
                                                       api_namespace=parent_ns))
            resources.append(PublicLambdaProxyMethod(namespace=child_ns,
                                                     api_namespace=parent_ns,
                                                     function_namespace=endpoint["action"],
                                                     method=endpoint["method"],
                                                     parameters=endpoint["parameters"]))
        if "schema" in endpoint:
            resources.append(SchemaRequestValidator(namespace=child_ns,
                                                    api_namespace=parent_ns))
            resources.append(PublicLambdaProxyMethod(namespace=child_ns,
                                                     api_namespace=parent_ns,
                                                     function_namespace=endpoint["action"],
                                                     method=endpoint["method"],
                                                     schema=endpoint["schema"]))
            resources.append(Model(namespace=child_ns,
                                   api_namespace=parent_ns,
                                   schema=endpoint["schema"]))
        return resources
            
if __name__=="__main__":
    api=PublicApi(namespace="hello-api",
                  endpoints=[{"action": "whatevs",
                              "method": "GET",
                              "path": "hello-get",
                              "parameters": ["message"]},
                             {"action": "whatevs",
                              "method": "POST",
                              "path": "hello-post",
                              "schema": {"hello": "world"}}])                             
    import json
    print (json.dumps(api.render(),
                      indent=2))
    
