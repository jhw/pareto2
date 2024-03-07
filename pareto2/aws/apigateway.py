from pareto2.aws import hungarorise as H

"""
- distinguish between aws.Resource and apigw.Resource
"""

# from pareto2.aws import Resource
from pareto2 import aws

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
            "DeploymentId": {"Ref": H(f"{self.component_name}-deployment")}
        }

    @property
    def depends(self):
        return [H(f"{self.component_name}-method"),
                H(f"{self.component_name}-cors-method")]
                
class Stage(aws.Resource):

    def __init__(self, component_name, stage_name="prod"):
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

    def __init__(self, component_name, pathpart):
        self.component_name = component_name
        self.pathpart = pathpart

    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.component_name}-rest-api"), "RootResourceId"]}.
            "PathPart": self.pathpart,
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")}
        }

class Method(aws.Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

class Authorizer(aws.Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        return {
            "ProviderARNS": [{"Fn::GetAtt": [H(f"{self.component_name}-user-pool"), "Arn"]}],
            "IdentitySource": "method.request.header.Authorization",
            "Name": {"Fn::Sub": H(f"{self.component_name}-authorizer-${{AWS::StackName}}")},
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "Type": "COGNITO_USER_POOLS"
        }

class RequestValidator(aws.Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        props = {"RestApiId": {"Ref": H(f"{self.component_name}-rest-api")}}
        validation_settings = self.validation_settings()
        props.update(validation_settings)
        return props

    def validation_settings(self):
        """Method to be implemented by subclasses for specific validation settings."""
        return {}

class Model(aws.Resource):
    
    def __init__(self, component_name, content_type="application/json"):
        self.component_name = component_name
        self.content_type = content_type

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "ContentType": self.content_type,
            "Name": self.component_name,
            "Schema": self.schema()
        }

class GatewayResponse(aws.Resource):
    
    def __init__(self, component_name, response_type):
        self.component_name = component_name
        self.response_type = response_type

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "ResponseType": self.response_type,
            "ResponseParameters": self.response_parameters()
        }

class DomainName(aws.Resource):

    def __init__(self, component_name, domain_name, certificate_arn):
        self.component_name = component_name
        self.domain_name = domain_name
        self.certificate_arn = certificate_arn

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": self.domain_name},
            "CertificateArn": {"Ref": self.certificate_arn}
        }
    
class BasePathMapping(aws.Resource):

    def __init__(self, component_name, domain_name, stage_name):
        self.component_name = component_name
        self.domain_name = domain_name
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": self.domain_name},
            "RestApiId": {"Ref": H(f"{self.component_name}-rest-api")},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [H(f"{self.component_name}-domain-name")]
