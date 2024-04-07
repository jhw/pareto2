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

class RedirectMethod(Method):

    def __init__(self, namespace, api_namespace, path = "index.html"):
        super().__init__(namespace = namespace)
        self.api_namespace = api_namespace
        self.path = path

    @property
    def _integration(self):
        request_templates = {"application/json": "{\"statusCode\" : 302}"}
        domain_name_ref = H("domain-name")
        redirect_url = {"Fn::Sub": f"'https://${{{domain_name_ref}}}/{self.path}'"}
        integration_responses = [{"StatusCode": 302,
                                  "ResponseTemplates": {"application/json": "{}"},
                                  "ResponseParameters": {"method.response.header.Location": redirect_url}}]
        return {"Type": "MOCK",
                "RequestTemplates": request_templates,
                "IntegrationResponses": integration_responses}      
        
    @property
    def aws_properties(self):
        method_responses = [{"StatusCode": 302,
                             "ResponseParameters": {"method.response.header.Location": True}}]
        resource_id = {"Fn::GetAtt": [H(f"{self.api_namespace}-rest-api"), "RootResourceId"]}
        return {"HttpMethod": "GET",
                "AuthorizationType": "NONE",
                "MethodResponses": method_responses,
                "Integration": self._integration,
                "ResourceId": resource_id, 
                "RestApiId": {"Ref": H(f"{self.api_namespace}-rest-api")}}

"""
This is not currently CORS enabled. You could do it but it would be a big ball ache. You would need to define a CorsMethod which did all the CORS pre- flight stuff. This is possible, the code exists in branches from approx 23/03/24 - 30/03/24. But then you would also need ProxyMethod to return the CORS headers that the Lambda does in the APIGatewayV2 web-api recipe. All in all it's probably too much of a pain - this is supposed to be a simple pattern! If you really need CORS then you are probably better relying on the web-api recipe.
"""

"""
BinaryMediaTypes = ["*/*"] is required if you want to get this pattern to serve any kind of binary data from S3; but enabling it messes up the redirect; hence the either/or switch enabled by has_binary_media. As per CORS, I am simply not willing to wrestle with APIGateway any more to fix this, in what is likely to be a minority- use pattern.
"""

class Website(Recipe):    

    def __init__(self, namespace, binary_media = True):
        super().__init__()
        self.append(RestApi(namespace = namespace,
                            binary_media_types = ["*/*"] if binary_media else []))
        for klass in [Stage,
                      ProxyResource,
                      ProxyRole,
                      ProxyPolicy,
                      DomainName,
                      BasePathMapping,
                      DistributionRecordSet, # NB                   
                      StreamBucket]:
            self.append(klass(namespace = namespace))
        method_attrs = ["proxy", "redirect"] if not binary_media else ["proxy"]            
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

    
