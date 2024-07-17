from pareto2.services import hungarorise as H
from pareto2.services.apigateway import *
from pareto2.services.apigateway import Resource as APIGWResource
from pareto2.services.iam import *
from pareto2.services.route53 import *
from pareto2.services.s3 import *
from pareto2.recipes import *

class ProxyResource(APIGWResource):

    def __init__(self, namespace, path = "{proxy+}"):
        super().__init__(namespace = namespace,
                         path = path)

class ProxyMethod(Method):

    def __init__(self, namespace, api_namespace):
        super().__init__(namespace = namespace)
        self.api_namespace = api_namespace

    @property
    def _integration(self):
        uri = {"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:s3:path/${%s}/{proxy}" % H(f"{self.api_namespace}-bucket")}
        credentials = {"Fn::GetAtt": [H(f"{self.api_namespace}-role"), "Arn"]}
        request_parameters = {"integration.request.path.proxy": "method.request.path.proxy"}
        integration_responses = [{"StatusCode": 200,
                                  "ResponseParameters": {"method.response.header.Content-Type": "integration.response.header.Content-Type"}},
                                 {"StatusCode": 404,
                                  "SelectionPattern": "404"}]
        return {"IntegrationHttpMethod": "ANY",
                "Type": "AWS",
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "Uri": uri,
                "Credentials": credentials,
                "RequestParameters": request_parameters, 
                "IntegrationResponses": integration_responses}    
        
    @property
    def aws_properties(self):
        request_parameters = {"method.request.path.proxy": True}
        method_responses = [{"StatusCode": 200,
                             "ResponseParameters": {"method.response.header.Content-Type": True}},
                            {"StatusCode": 404}]
        return {"HttpMethod": "GET",
                "AuthorizationType": "NONE",
                "RequestParameters": request_parameters,
                "MethodResponses": method_responses,
                "Integration": self._integration,
                "ResourceId": {"Ref": H(f"{self.api_namespace}-resource")},
                "RestApiId": {"Ref": H(f"{self.api_namespace}-rest-api")}}
    
class ProxyRole(Role):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         principal = "apigateway.amazonaws.com")

class ProxyPolicy(Policy):

    def __init__(self, namespace):
        bucket_ref = H(f"{namespace}-bucket")
        permissions = [{"action": "s3:GetObject",
                        "resource": {"Fn::Sub": f"arn:aws:s3:::${{{bucket_ref}}}/*"}}]
        super().__init__(namespace = namespace,
                         permissions = permissions)

"""
This is not currently CORS enabled. You could do it but it would be a big ball ache. You would need to define a CorsMethod which did all the CORS pre- flight stuff. This is possible, the code exists in branches from approx 23/03/24 - 30/03/24. But then you would also need ProxyMethod to return the CORS headers that the Lambda does in the APIGatewayV2 web-api recipe. All in all it's probably too much of a pain - this is supposed to be a simple pattern! If you really need CORS then you are probably better relying on the web-api recipe.
"""

class Website(Recipe):    

    def __init__(self, namespace):
        super().__init__()
        self.append(RestApi(namespace = namespace))
        for klass in [Stage,
                      ProxyResource,
                      ProxyRole,
                      ProxyPolicy,
                      DomainName,
                      BasePathMapping,
                      DistributionRecordSet, # NB                   
                      StreamingBucket]:
            self.append(klass(namespace = namespace))
        method_attrs = ["proxy"]
        for attr in method_attrs:
            klass = eval("%sMethod" % attr.capitalize())
            self.append(klass(namespace = f"{namespace}-{attr}",
                              api_namespace = namespace))
        method_refs = [H(f"{namespace}-{attr}-method")
                       for attr in method_attrs]
        self.append(Deployment(namespace = namespace,
                               methods = method_refs))

if __name__ == "__main__":
    pass

    
