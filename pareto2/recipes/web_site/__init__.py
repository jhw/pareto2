from pareto2.services import hungarorise as H

from pareto2.services.apigateway import *
from pareto2.services.apigateway import Resource as APIGWResource
from pareto2.services.iam import *
from pareto2.services.route53 import *
from pareto2.services.s3 import *

from pareto2.recipes import Recipe

import re

def dehungarorise(text):
    buf, tok = [], ""
    for c in text:
        if c.upper() == c:
            if tok != "":
                buf.append(tok)
            tok = c.lower()
        else:
            tok += c
    if tok != "":
        buf.append(tok)
    return "-".join(buf)

class AltNamespaceMixin:

    @property
    def resource_name(self):    
        tokens = self.class_names[-1].split(".") # latest subclass
        return "%s-%s" % (self.namespace, dehungarorise(tokens[-1]))

class RedirectMethod(AltNamespaceMixin, Method):

    def __init__(self, namespace, path = "index.html"):
        super().__init__(namespace = namespace)
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
        resource_id = {"Fn::GetAtt": [H(f"{self.namespace}-rest-api"), "RootResourceId"]}
        return {"HttpMethod": "GET",
                "AuthorizationType": "NONE",
                "MethodResponses": method_responses,
                "Integration": self._integration,
                "ResourceId": resource_id, 
                "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}}
        
class ProxyResource(APIGWResource):

    def __init__(self, namespace, path = "{proxy+}"):
        super().__init__(namespace = namespace,
                         path = path)

class ProxyMethod(AltNamespaceMixin, Method):

    def __init__(self, namespace):
        super().__init__(namespace = namespace)

    @property
    def _integration(self):
        uri = {"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:s3:path/${%s}/{proxy}" % H(f"{self.namespace}-bucket")}
        credentials = {"Fn::GetAtt": [H(f"{self.namespace}-role"), "Arn"]}
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
                "ResourceId": {"Ref": H(f"{self.namespace}-resource")},
                "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}}
    
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

class WebSite(Recipe):    

    def __init__(self, namespace):
        super().__init__()
        for fn in [self.init_rest_api]:
            self.append(fn(namespace))
        for klass in [Stage,
                      ProxyResource,
                      ProxyMethod,
                      ProxyRole,
                      ProxyPolicy,
                      RedirectMethod,
                      DomainName,
                      BasePathMapping,
                      RecordSet,                      
                      StreamingBucket]:
            self.append(klass(namespace = namespace))
        for fn in [self.init_deployment]:
            self.append(fn(namespace))

    def init_rest_api(self, namespace):
        return RestApi(namespace = namespace,
                       binary_media_types = "*/*")
            
    def init_deployment(self, namespace):        
        method_refs = [H(f"{namespace}-proxy-method"),
                       H(f"{namespace}-redirect-method")]
        return Deployment(namespace = namespace,
                          methods = method_refs)
            
if __name__ == "__main__":
    pass

    
