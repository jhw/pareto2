from pareto2.aws import hungarorise as H

# from pareto2.aws import Resource
from pareto2.aws import Resource as AWSResource # distinguish between aws.Resource and apigw.Resource

import json

LambdaProxyMethodArn="arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

StageName="prod"

class RestApi(AWSResource):

    def __init__(self, name):
        self.name = name

    @property
    def aws_properties(self):
        return {
            "Name": {"Fn::Sub": f"{self.name}-rest-api-${{AWS::StackName}}"}
        }

class Deployment(AWSResource):

    def __init__(self, name):
        self.name = name

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")}
        }

    @property
    def depends(self):
        return [H(f"{self.name}-method"),
                H(f"{self.name}-cors-method")]
                
class Stage(AWSResource):

    def __init__(self, name, stage_name=StageName):
        self.name = name
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "StageName": self.stage_name,
            "DeploymentId": {"Ref": H(f"{self.name}-deployment")},
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")}
        }
    
class Resource(AWSResource):

    def __init__(self, name, path):
        self.name = name
        self.path = path

    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.name}-rest-api"), "RootResourceId"]},
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")}
        }

class Method(AWSResource):
    
    def __init__(self, name):
        self.name = name

class LambdaProxyMethod(Method):

    def __init__(self, name, parameters = None, schema = None):
        Method.__init__(self, name)
        self.parameters = parameters
        self.schema = schema

    """
    - replace api, endpoint with constructor arg
    - resource defined on per api or per- endpoint basis?
    """
        
    @property
    def aws_properties(self):
        uri={"Fn::Sub": [LambdaProxyMethodArn, {"arn": {"Fn::GetAtt": [H("%s-function" % endpoint["action"]), "Arn"]}}]}
        integration={"IntegrationHttpMethod": "POST",
                     "Type": "AWS_PROXY",
                     "Uri": uri}
        props={"HttpMethod": endpoint["method"],
               "Integration": integration,
               "ResourceId": {"Ref": H("%s-resource" % endpoint["name"])},
               "RestApiId": {"Ref": H("%s-rest-api" % api["name"])}}
        props.update(authorisation)
        if self.parameters:
            props["RequestValidatorId"]={"Ref": H("%s-validator" % endpoint["name"])}
            props["RequestParameters"]={"method.request.querystring.%s" % param: True
                                        for param in self.parameters}
        if self.schema:
            props["RequestValidatorId"]={"Ref": H("%s-validator" % endpoint["name"])}
            props["RequestModels"]={"application/json": H("%s-model" % endpoint["name"])}
        return props

class PublicLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, name, **kwargs):
        LambdaProxyMethod.__init__(self, name, **kwargs)

class PrivateLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, name, **kwargs):
        LambdaProxyMethod.__init__(self, name, **kwargs)
        
class CorsMethod(Method):

    def __init__(self, name, method):
        Method.__init__(self, name)
        self.method = method

    def _integration_response(self):
        params={"method.response.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", ",".join(CorsHeaders)),
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
                "ResourceId": {"Ref": H(f"{self.name}-resource")}, # API resource or endpoint resource?
                "RestApiId": {"Ref": H(f"{self.name}-rest-api")}}
        
class Authorizer(AWSResource):
    
    def __init__(self, name):
        self.name = name

    """
    - feels like all APIGW authentication is going to be done against a UserPool, so it's okay to make this Cognito- centric in a base class
    """
        
    @property
    def aws_properties(self):
        return {
            "ProviderARNS": [{"Fn::GetAtt": [H(f"{self.name}-user-pool"), "Arn"]}],
            "IdentitySource": "method.request.header.Authorization",
            "Name": {"Fn::Sub": H(f"{self.name}-authorizer-${{AWS::StackName}}")},
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")},
            "Type": "COGNITO_USER_POOLS"
        }

class RequestValidator(AWSResource):

    def __init__(self, name, validate_request_parameters=False, validate_request_body=False):
        self.name = name
        self.validate_request_parameters = validate_request_parameters
        self.validate_request_body = validate_request_body

    @property
    def aws_properties(self):
        return {"RestApiId": {"Ref": H(f"{self.name}-rest-api")},
                "ValidateRequestParameters": self.validate_request_parameters,
                "ValidateRequestBody": self.validate_request_body}

class RequestValidatorGET(RequestValidator):

    def __init__(self, name):
        return RequestValidator.__init__(self, name, validate_request_parameters=True)

class RequestValidatorPOST(RequestValidator):

    def __init__(self, name):
        return RequestValidator.__init__(self, name, validate_request_body=True)

"""
- pareto 0-7 notes say Name is "optional" but is in fact required if Method is to be able to look up model :/
"""

class Model(AWSResource):
    
    def __init__(self,
                 name,
                 schema,
                 schema_type="http://json-schema.org/draft-04/schema#",
                 content_type="application/json"):
        self.name = name
        self.schema = schema
        if "$schema" not in self.schema:
            self.schema["$schema"] = self.schema_type
        self.content_type = content_type

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")},
            "ContentType": self.content_type,
            "Name": self.name, # required?
            "Schema": schema
        }

class GatewayResponse(AWSResource):

    def __init__(self, name, response_type):
        self.name = name
        self.response_type = response_type

    @property
    def aws_properties(self):
        params={"gatewayresponse.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", "*"),
                             ("origin", "*")]}
        return {
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")},
            "ResponseType": "DEFAULT_%s" % self.response_type,
            "ResponseParameters": params
        }

class GatewayResponse4XX(GatewayResponse):

    def __init__(self, name):
        return GatewayResponse.__init__(self, name, response_type="4XX")

class GatewayResponse5XX(GatewayResponse):

    def __init__(self, name):
        return GatewayResponse.__init__(self, name, response_type="5XX")
        
class DomainName(AWSResource):

    def __init__(self, name):
        self.name = name

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")},
            "DomainName": {"Ref": H("domain-name")},
            "CertificateArn": {"Ref": H("certificate-arn")}
        }
    
class BasePathMapping(AWSResource):

    def __init__(self, name, stage_name=StageName):
        self.name = name
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "RestApiId": {"Ref": H(f"{self.name}-rest-api")},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [H(f"{self.name}-domain-name")]
