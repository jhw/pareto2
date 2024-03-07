from pareto2.aws import hungarorise as H

"""
- distinguish between aws.Resource and apigw.Resource
"""

# from pareto2.aws import Resource
from pareto2 import aws

StageName="prod"

class RestApi(aws.Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        return {
            "Name": {"Fn::Sub": H(f"{self.component_name}-rest-api-${{AWS::StackName}}")}
        }

class Deployment(aws.Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")}
        }

    @property
    def depends(self):
        return [H(f"{self.component_name}-method"),
                H(f"{self.component_name}-cors-method")]
                
class Stage(aws.Resource):

    def __init__(self, component_name, stage_name=StageName):
        self.component_name = component_name
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "StageName": self.stage_name,
            "DeploymentId": {"Ref": H(f"{self.component_name}-deployment")},
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")}
        }
    
class Resource(aws.Resource):

    def __init__(self, component_name, path):
        self.component_name = component_name
        self.path = path

    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.component_name}-rest-api"), "RootResourceId"]}.
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")}
        }

class Method(aws.Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

class Authorizer(aws.Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

    """
    - feels like all APIGW authentication is going to be done against a UserPool, so it's okay to make this Cognito- centric in a base class
    """
        
    @property
    def aws_properties(self):
        return {
            "ProviderARNS": [{"Fn::GetAtt": [H(f"{self.component_name}-user-pool"), "Arn"]}],
            "IdentitySource": "method.request.header.Authorization",
            "Name": {"Fn::Sub": H(f"{self.component_name}-authorizer-${{AWS::StackName}}")},
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "Type": "COGNITO_USER_POOLS"
        }

class RequestValidatorBase(aws.Resource):

    def __init__(self, component_name, validate_request_parameters=False, validate_request_body=False):
        self.component_name = component_name
        self.validate_request_parameters = validate_request_parameters
        self.validate_request_body = validate_request_body

    @property
    def aws_properties(self):
        return {"RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
                "ValidateRequestParameters": self.validate_request_parameters,
                "ValidateRequestBody": self.validate_request_body}

class RequestValidatorGET(RequestValidatorBase):

    def __init__(self, component_name):
        return RequestValidatorBase.__init__(self, component_name, validate_request_parameters=True)

class RequestValidatorPOST(RequestValidatorBase):

    def __init__(self, component_name):
        return RequestValidatorBase.__init__(self, component_name, validate_request_body=True)

"""
- pareto 0-7 notes say Name is "optional" but is in fact required if Method is to be able to look up model :/
"""

class Model(aws.Resource):
    
    def __init__(self,
                 component_name,
                 schema,
                 schema_type="http://json-schema.org/draft-04/schema#",
                 content_type="application/json"):
        self.component_name = component_name
        self.schema = schema
        if "$schema" not in self.schema:
            self.schema["$schema"] = self.schema_type
        self.content_type = content_type

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "ContentType": self.content_type,
            "Name": self.component_name, # required?
            "Schema": schema
        }

class GatewayResponseBase(aws.Resource):

    def __init__(self, component_name, response_type):
        self.component_name = component_name
        self.response_type = response_type

    @property
    def aws_properties(self):
        params={"gatewayresponse.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", "*"),
                             ("origin", "*")]}
        return {
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "ResponseType": "DEFAULT_%s" % self.response_type,
            "ResponseParameters": self.response_parameters()
        }

class GatewayResponse4XX(GatewayResponseBase):

    def __init__(self, component_name):
        return GatewayResponseBase.__init__(self, component_name, response_code="4XX")

class GatewayResponse5XX(GatewayResponseBase):

    def __init__(self, component_name):
        return GatewayResponseBase.__init__(self, component_name, response_code="5XX")
        
class DomainName(aws.Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "DomainName": {"Ref": H("domain-name")},
            "CertificateArn": {"Ref": H("certificate-arn")}
        }
    
class BasePathMapping(aws.Resource):

    def __init__(self, component_name, stage_name=StageName):
        self.component_name = component_name
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [H(f"{self.component_name}-domain-name")]
