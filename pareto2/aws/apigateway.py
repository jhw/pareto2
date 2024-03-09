from pareto2.aws import hungarorise as H

# from pareto2.aws import Resource
from pareto2.aws import Resource as AWSResource # distinguish between aws.Resource and apigw.Resource

import json

LambdaProxyMethodArn="arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

StageName="prod"

CORSHeaders=["Content-Type",
             "X-Amz-Date",
             "Authorization",
             "X-Api-Key",
             "X-Amz-Sec"]

class RestApi(AWSResource):

    def __init__(self, namespace):
        self.namespace = namespace

    """
    - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-restapi.html
    - The name of the RestApi. A name is required if the REST API is not based on an OpenAPI specification
    - generally a good idea to include AWS::StackName in case Name exists in a global namespace
    """
        
    @property
    def aws_properties(self):
        return {
            "Name": {"Fn::Sub": f"{self.namespace}-rest-api-${{AWS::StackName}}"}
        }

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

    def __init__(self, namespace, stage_name=StageName):
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

    def __init__(self, namespace, api_namespace, path):
        self.namespace = namespace
        self.api_namespace = api_namespace
        self.path = path

    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.api_namespace}-rest-api"), "RootResourceId"]},
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.api_namespace}-rest-api")}
        }

class Method(AWSResource):
    
    def __init__(self, namespace, api_namespace):
        self.namespace = namespace
        self.api_namespace = api_namespace

class LambdaProxyMethod(Method):

    def __init__(self,
                 namespace,
                 api_namespace,
                 function_namespace,
                 method,
                 authorisation = None,
                 parameters = None,
                 schema = None):
        super().__init__(namespace, api_namespace)
        self.function_namespace = function_namespace
        self.method = method
        self.authorisation = authorisation
        self.parameters = parameters
        self.schema = schema
        
    @property
    def aws_properties(self):
        uri={"Fn::Sub": [LambdaProxyMethodArn, {"arn": {"Fn::GetAtt": [H(f"{self.function_namespace}-function"), "Arn"]}}]}
        integration={"IntegrationHttpMethod": "POST",
                     "Type": "AWS_PROXY",
                     "Uri": uri}
        props={"HttpMethod": self.method,
               "Integration": integration,
               "ResourceId": {"Ref": H("%s-resource" % self.namespace)},
               "RestApiId": {"Ref": H("%s-rest-api" % self.api_namespace)}}
        props.update(self.authorisation)
        if self.parameters:
            props["RequestValidatorId"]={"Ref": H("%s-validator" % self.namespace)}
            props["RequestParameters"]={"method.request.querystring.%s" % param: True
                                        for param in self.parameters}
        if self.schema:
            props["RequestValidatorId"]={"Ref": H("%s-validator" % self.namespace)}
            props["RequestModels"]={"application/json": H("%s-model" % self.namespace)}
        return props

class PublicLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, api_namespace, **kwargs):
        super().__init__(namespace,
                         api_namespace,
                         authorisation={"AuthorizationType": "NONE"},
                         **kwargs)

class PrivateLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, api_namespace, **kwargs):
        super().__init__(namespace,
                         api_namespace,
                         authorisation={"Authorization": "COGNITO",
                                        "Authorizer": {"Ref": H("%s-authorizer" % namespace)}},
                         **kwargs)
        
class CORSMethod(Method):

    def __init__(self, namespace, api_namespace, method):
        super().__init__(namespace, api_namespace)
        self.method = method
        
    def _integration_response(self, cors_headers=CORSHeaders):
        params={"method.response.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", ",".join(cors_headers)),
                             ("methods", "%s,OPTIONS" % self.method),
                             ("origin", "*")]}
        templates={"application/json": ""}
        return {"StatusCode": 200,
                "ResponseParameters": params,
                "ResponseTemplates": templates}

    def _integration(self):
        templates={"application/json": json.dumps({"statusCode": 200})}
        response=self._integration_response()
        return {"IntegrationResponses": [response],
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "RequestTemplates": templates,
                "Type": "MOCK"}

    def _response(self):
        params={"method.response.header.Access-Control-Allow-%s" % k.capitalize(): False
                for k in ["headers", "methods", "origin"]}
        models={"application/json": "Empty"}
        return {"StatusCode": 200,
                "ResponseModels": models,
                "ResponseParameters": params}
        
    @property
    def aws_properties(self):
        integration=self._integration()
        response=self._response()
        return {"AuthorizationType": "NONE",
                "HttpMethod": "OPTIONS",
                "Integration": integration,
                "MethodResponses": [response],
                "ResourceId": {"Ref": H(f"{self.namespace}-resource")}, # API resource or endpoint resource?
                "RestApiId": {"Ref": H(f"{self.api_namespace}-rest-api")}}
        
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
            "Name": {"Fn::Sub": H(f"{self.namespace}-authorizer-${{AWS::StackName}}")},
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "Type": "COGNITO_USER_POOLS"
        }

class RequestValidator(AWSResource):

    def __init__(self, namespace, api_namespace, validate_request_parameters=False, validate_request_body=False):
        self.namespace = namespace
        self.api_namespace = api_namespace
        self.validate_request_parameters = validate_request_parameters
        self.validate_request_body = validate_request_body

    @property
    def aws_properties(self):
        return {"RestApiId": {"Ref": H(f"{self.api_namespace}-rest-api")},
                "ValidateRequestParameters": self.validate_request_parameters,
                "ValidateRequestBody": self.validate_request_body}

class ParameterRequestValidator(RequestValidator):

    def __init__(self, namespace, api_namespace):
        return super().__init__(namespace, api_namespace, validate_request_parameters=True)

class SchemaRequestValidator(RequestValidator):

    def __init__(self, namespace, api_namespace):
        return super().__init__(namespace, api_namespace, validate_request_body=True)


class Model(AWSResource):
    
    def __init__(self,
                 namespace,
                 api_namespace,
                 schema,
                 schema_type="http://json-schema.org/draft-04/schema#",
                 content_type="application/json"):
        self.namespace = namespace
        self.api_namespace = api_namespace
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
            "RestApiId": {"Ref": H(f"{self.api_namespace}-rest-api")},
            "ContentType": self.content_type,
            # "Name": {"Fn::Sub": f"{self.namespace}-model-${{AWS::StackName}}"},
            "Schema": self.schema
        }

class GatewayResponse(AWSResource):

    def __init__(self, namespace, response_type):
        self.namespace = namespace
        self.response_type = response_type

    @property
    def aws_properties(self):
        params={"gatewayresponse.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", "*"),
                             ("origin", "*")]}
        return {
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "ResponseType": "DEFAULT_%s" % self.response_type,
            "ResponseParameters": params
        }

class GatewayResponse4XX(GatewayResponse):

    def __init__(self, namespace):
        return super().__init__(namespace, response_type="4XX")

class GatewayResponse5XX(GatewayResponse):

    def __init__(self, namespace):
        return super().__init__(namespace, response_type="5XX")
        
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

    def __init__(self, namespace, stage_name=StageName):
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
