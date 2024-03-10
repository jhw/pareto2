from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as APIGWResource
from pareto2.aws.cognito import *
from pareto2.aws.route53 import *

from pareto2.components import Component
from pareto2.components.api import Permission

import re

class PublicApi(Component):    

    def __init__(self, namespace, endpoints):
        super().__init__()
        self += self.init_api(namespace)
        for endpoint in endpoints:
            self += self.init_endpoint(namespace, endpoint)
        methods = self.filter_methods(namespace, endpoints)
        self += self.init_deployment(namespace, methods)

    def init_api(self, namespace):
        return [klass(namespace=namespace)
                for klass in [RestApi,
                              Stage,
                              GatewayResponse4XX,
                              GatewayResponse5XX,
                              DomainName,
                              BasePathMapping,
                              RecordSet]]

    def filter_methods(self, parent_ns, endpoints):
        methods = []
        for endpoint in endpoints:
            child_ns = self.endpoint_namespace(parent_ns, endpoint)
            methods += [H(f"{child_ns}-public-lambda-proxy-method"),
                        H(f"{child_ns}-cors-method")]
        return methods
    
    def init_deployment(self, namespace, methods):
        return [Deployment(namespace=namespace,
                           methods=methods)]
    
    def endpoint_namespace(self, namespace, endpoint):
        return "%s-%s" % (namespace,
                          "-".join([tok.lower()
                                    for tok in re.split("\\W", endpoint["path"])
                                    if tok != ""]))
    
    def init_endpoint(self, parent_ns, endpoint):
        child_ns = self.endpoint_namespace(parent_ns, endpoint)
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
    pass

    
