from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as APIGWResource
from pareto2.aws.cognito import *
from pareto2.aws.route53 import *

from pareto2.components import Component

def init_GET_endpoint(name, endpoint):
    return [APIGWResource(name=name,
                          path=endpoint["path"]),
            PublicLambdaProxyMethod(name=name,
                                    function_name="whatevs",
                                    method=endpoint["method"],
                                    parameters=endpoint["parameters"])]

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
            if endpoint["method"].upper()=="GET":
                self += init_GET_endpoint(name, endpoint)
            elif endpoint["method"].upper()=="POST":
                pass
            else:
                raise RuntimeError("endpoint method %s not recognised" % endpoint["method"])

if __name__=="__main__":
    api=PublicApi(name="hello-api",
                  endpoints=[{"name": "hello-get",
                              "method": "GET",
                              "path": "hello",
                              "parameters": ["message"]}])
                             
    import json
    print (json.dumps(api.render(),
                      indent=2))
    
