from pareto2.services import hungarorise as H

# from pareto2.services import Resource
from pareto2.services import Resource as AWSResource # distinguish between aws.Resource and apigw.Resource

import json

LambdaProxyMethodArn = "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

StageName = "prod"

CorsHeaders = ["Content-Type",
               "X-Amz-Date",
               "Authorization",
               "X-Api-Key",
               "X-Amz-Sec"]

class RestApi(AWSResource):

    def __init__(self, namespace, binary_media_types = None):
        self.namespace = namespace
        self.binary_media_types = binary_media_types

    """
    - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-restapi.html
    - The name of the RestApi. A name is required if the REST API is not based on an OpenAPI specification
    - generally a good idea to include AWS::StackName in case Name exists in a global namespace
    """
        
    @property
    def aws_properties(self):
        props = {
            "Name": {"Fn::Sub": f"{self.namespace}-rest-api-${{AWS::StackName}}"}
        }
        if self.binary_media_types:
            props["BinaryMediaTypes"] = self.binary_media_types
        return props

    @property
    def visible(self):
        return True
    
class Deployment(AWSResource):

    def __init__(self, namespace, methods):
        self.namespace = namespace
        self.methods = methods

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}
        }

    @property
    def depends(self):
        return self.methods
                
class Stage(AWSResource):

    def __init__(self, namespace, stage_name = StageName):
        self.namespace = namespace
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "StageName": self.stage_name,
            "DeploymentId": {"Ref": H(f"{self.namespace}-deployment")},
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}
        }

class Resource(AWSResource):

    def __init__(self, namespace, path):
        self.namespace = namespace
        self.path = path

    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.namespace}-rest-api"), "RootResourceId"]},
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}
        }

    """
    - occasionally a subclassed resource might override resource_name to point to base_resource_name
    - this is so other resources in the same module can refer to this class using standard #{namespace}-#{resource-name} nomenclature, without having to know the name of the specific subclass
    """

    @property
    def resource_name(self):
        return self.base_resource_name
    
class S3ProxyResource(Resource):

    def __init__(self, namespace, path = "{proxy+}"):
        super().__init__(namespace, path)
    
"""
- LambdaProxyResource doesn't use namespace directly, but still needs to live in its own namespace because a single API might have multiple endpoints, each with their own resources
"""
        
class LambdaProxyResource(Resource):

    def __init__(self, namespace, parent_namespace, path):
        super().__init__(namespace, path)
        self.parent_namespace = parent_namespace
        
    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.parent_namespace}-rest-api"), "RootResourceId"]},
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")}
        }

class Method(AWSResource):
    
    def __init__(self, namespace):
        self.namespace = namespace

class RootRedirectMethod(Method):

    def __init__(self, namespace, path = "index.html"):
        super().__init__(namespace)
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
        
class S3ProxyMethod(Method):

    def __init__(self, namespace):
        super().__init__(namespace)

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
        
class LambdaProxyMethod(Method):

    def __init__(self,
                 namespace,
                 parent_namespace,
                 function_namespace,
                 method,
                 authorisation = None,
                 parameters = None,
                 schema = None):
        super().__init__(namespace)
        self.parent_namespace = parent_namespace
        self.function_namespace = function_namespace
        self.method = method
        self.authorisation = authorisation
        self.parameters = parameters
        self.schema = schema
        
    @property
    def aws_properties(self):
        uri = {"Fn::Sub": [LambdaProxyMethodArn, {"arn": {"Fn::GetAtt": [H(f"{self.function_namespace}-function"), "Arn"]}}]}
        integration = {"IntegrationHttpMethod": "POST",
                       "Type": "AWS_PROXY",
                       "Uri": uri}
        props = {"HttpMethod": self.method,
                 "Integration": integration,
                 "ResourceId": {"Ref": H(f"{self.namespace}-resource")},
                 "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")}}
        props.update(self.authorisation)
        if self.parameters:
            props["RequestValidatorId"] = {"Ref": H(f"{self.namespace}-parameter-request-validator")}
            props["RequestParameters"] = {f"method.request.querystring.{param}": True
                                        for param in self.parameters}
        if self.schema:
            props["RequestValidatorId"] = {"Ref": H(f"{self.namespace}-schema-request-validator")}
            props["RequestModels"] = {"application/json": H(f"{self.namespace}-model")}
        return props

class PublicLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "NONE"},
                         **kwargs)

class PrivateLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"Authorization": "COGNITO",
                                          "Authorizer": {"Ref": H(f"{parent_namespace}-authorizer")}},
                         **kwargs)
        
class CorsMethod(Method):

    def __init__(self, namespace, parent_namespace, method):
        super().__init__(namespace)
        self.parent_namespace = parent_namespace
        self.method = method

    @property
    def _integration_response(self, cors_headers = CorsHeaders):
        parameters = {"method.response.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                      for k, v in [("headers", ",".join(cors_headers)),
                                   ("methods", f"{self.method},OPTIONS"),
                                   ("origin", "*")]}
        templates = {"application/json": ""}
        return {"StatusCode": 200,
                "ResponseParameters": parameters,
                "ResponseTemplates": templates}

    @property
    def _integration(self):
        templates = {"application/json": json.dumps({"statusCode": 200})}
        return {"IntegrationResponses": [self._integration_response],
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "RequestTemplates": templates,
                "Type": "MOCK"}

    @property
    def _method_responses(self):
        response_parameters = {"method.response.header.Access-Control-Allow-%s" % k.capitalize(): False
                               for k in ["headers", "methods", "origin"]}
        response_models = {"application/json": "Empty"}
        return [{"StatusCode": 200,
                 "ResponseModels": response_models,
                 "ResponseParameters": response_parameters}]
        
    @property
    def aws_properties(self):
        return {"AuthorizationType": "NONE",
                "HttpMethod": "OPTIONS",
                "Integration": self._integration,
                "MethodResponses": self._method_responses,
                "ResourceId": {"Ref": H(f"{self.namespace}-resource")},
                "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")}}
        
class Authorizer(AWSResource):
    
    def __init__(self, namespace):
        self.namespace = namespace

    """
    - feels like all APIGW authentication is going to be done against a UserPool, so it's okay to make this Cognito- centric in a base class
    """
        
    @property
    def aws_properties(self):
        return {
            "ProviderARNS": [{"Fn::GetAtt": [H(f"{self.namespace}-user-pool"), "Arn"]}],
            "IdentitySource": "method.request.header.Authorization",
            "Name": {"Fn::Sub": f"{self.namespace}-authorizer-${{AWS::StackName}}"},
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "Type": "COGNITO_USER_POOLS"
        }

class RequestValidator(AWSResource):

    def __init__(self, namespace, parent_namespace, validate_request_parameters = False, validate_request_body = False):
        self.namespace = namespace
        self.parent_namespace = parent_namespace
        self.validate_request_parameters = validate_request_parameters
        self.validate_request_body = validate_request_body

    @property
    def aws_properties(self):
        return {"RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")},
                "ValidateRequestParameters": self.validate_request_parameters,
                "ValidateRequestBody": self.validate_request_body}

class ParameterRequestValidator(RequestValidator):

    def __init__(self, namespace, parent_namespace):
        return super().__init__(namespace, parent_namespace, validate_request_parameters = True)

class SchemaRequestValidator(RequestValidator):

    def __init__(self, namespace, parent_namespace):
        return super().__init__(namespace, parent_namespace, validate_request_body = True)

class Model(AWSResource):
    
    def __init__(self,
                 namespace,
                 parent_namespace,
                 schema,
                 schema_type = "http://json-schema.org/draft-04/schema#",
                 content_type = "application/json"):
        self.namespace = namespace
        self.parent_namespace = parent_namespace
        self.schema = schema
        self.schema_type = schema_type
        if "$schema" not in self.schema:
            self.schema["$schema"] = self.schema_type
        self.content_type = content_type

    """
    - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-model.html
    - not clear if Name parameter is required or not; 
    """
        
    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")},
            "ContentType": self.content_type,
            "Name": {"Fn::Sub": f"{self.namespace}-model-${{AWS::StackName}}"},
            "Schema": self.schema
        }

class GatewayResponse(AWSResource):

    def __init__(self, namespace, response_type):
        self.namespace = namespace
        self.response_type = response_type

    @property
    def aws_properties(self):
        response_parameters = {"gatewayresponse.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                      for k, v in [("headers", "*"),
                                   ("origin", "*")]}
        return {
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "ResponseType": f"DEFAULT_{self.response_type}",
            "ResponseParameters": response_parameters
        }

class GatewayResponse4xx(GatewayResponse):

    def __init__(self, namespace):
        return super().__init__(namespace, response_type = "4XX")

class GatewayResponse5xx(GatewayResponse):

    def __init__(self, namespace):
        return super().__init__(namespace, response_type = "5XX")
        
class DomainName(AWSResource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "DomainName": {"Ref": H("domain-name")},
            "CertificateArn": {"Ref": H("certificate-arn")}
        }
    
class BasePathMapping(AWSResource):

    def __init__(self, namespace, stage_name = StageName):
        self.namespace = namespace
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-domain-name")]
