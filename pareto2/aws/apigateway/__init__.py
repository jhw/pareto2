class RestApi:

    def __init__(self, name, binary_media_types=None):
        self.name = name
        self.binary_media_types = binary_media_types

    @property
    def resource_name(self):
        return f"{self.name}-rest-api"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::RestApi"

    @property
    def aws_properties(self):
        properties = {
            "Name": {"Fn::Sub": f"{self.name}-rest-api-${{AWS::StackName}}"}
        }
        if self.binary_media_types:
            properties["BinaryMediaTypes"] = self.binary_media_types
        return properties

class Deployment:

    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-deployment"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Deployment"

class Stage:

    def __init__(self, name, stage_name, deployment_id, rest_api_id):
        self.name = name
        self.stage_name = stage_name
        self.deployment_id = deployment_id
        self.rest_api_id = rest_api_id

    @property
    def resource_name(self):
        return f"{self.name}-stage"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Stage"

    @property
    def aws_properties(self):
        return {
            "StageName": self.stage_name,
            "DeploymentId": {"Ref": self.deployment_id},
            "RestApiId": {"Ref": self.rest_api_id}
        }
    
class Resource:

    def __init__(self, name, rest_api, pathpart, parent_id="RootResourceId"):
        self.name = name
        self.rest_api = rest_api
        self.pathpart = pathpart
        self.parent_id = parent_id

    @property
    def resource_name(self):
        return f"{self.name}-resource"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Resource"

    @property
    def aws_properties(self):
        parent_id = {"Fn::GetAtt": [self.rest_api, self.parent_id]}
        return {
            "ParentId": parent_id,
            "PathPart": self.pathpart,
            "RestApiId": {"Ref": self.rest_api}
        }
    
class Method:
    
    def __init__(self, name, aws_resource_type="AWS::ApiGateway::Method", **kwargs):
        self.name = name
        self._aws_resource_type = aws_resource_type
        self.kwargs = kwargs

    @property
    def resource_name(self):
        return f"{self.name}-method"

    @property
    def aws_resource_type(self):
        return self._aws_resource_type

class Authorizer:
    
    def __init__(self, name, rest_api_id, authorizer_type, identity_source):
        self.name = name
        self.rest_api_id = rest_api_id
        self.authorizer_type = authorizer_type
        self.identity_source = identity_source

    @property
    def resource_name(self):
        return f"{self.name}-authorizer"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Authorizer"

    @property
    def aws_properties(self):
        return {
            "IdentitySource": self.identity_source,
            "Name": {"Fn::Sub": f"{self.name}-authorizer-${{AWS::StackName}}"},
            "RestApiId": {"Ref": self.rest_api_id},
            "Type": self.authorizer_type
        }

class RequestValidator:

    def __init__(self, api_name, rest_api_id):
        self.api_name = api_name
        self.rest_api_id = rest_api_id

    @property
    def resource_name(self):
        return f"{self.api_name}-api-validator"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::RequestValidator"

    @property
    def aws_properties(self):
        props = {"RestApiId": {"Ref": self.rest_api_id}}
        validation_settings = self.validation_settings()
        props.update(validation_settings)
        return props

    def validation_settings(self):
        """Method to be implemented by subclasses for specific validation settings."""
        return {}

class Model:
    
    def __init__(self, api_name, rest_api_id, name, content_type="application/json"):
        self.api_name = api_name
        self.rest_api_id = rest_api_id
        self.name = name
        self.content_type = content_type

    @property
    def resource_name(self):
        return f"{self.api_name}-api-model"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Model"

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": self.rest_api_id},
            "ContentType": self.content_type,
            "Name": self.name,
            "Schema": self.schema()
        }

class GatewayRespons:
    
    def __init__(self, api_name, response_type, rest_api_id):
        self.api_name = api_name
        self.response_type = response_type
        self.rest_api_id = rest_api_id

    @property
    def resource_name(self):
        return f"{self.api_name}-gateway-response-{self.response_type}"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::GatewayResponse"

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": self.rest_api_id},
            "ResponseType": self.response_type,
            "ResponseParameters": self.response_parameters()
        }

class DomainName:

    def __init__(self, name, domain_name="domain-name", certificate_arn="certificate-arn"):
        self.name = name
        self.domain_name = domain_name
        self.certificate_arn = certificate_arn

    @property
    def resource_name(self):
        return f"{self.name}-domain"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::DomainName"

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": self.domain_name},
            "CertificateArn": {"Ref": self.certificate_arn}
        }
    
class BasePathMapping:

    def __init__(self, name, domain_name="domain-name", stage_name="StageName"):
        self.name = name
        self.domain_name = domain_name
        self.stage_name = stage_name

    @property
    def resource_name(self):
        return f"{self.name}-domain-path-mapping"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::BasePathMapping"

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": self.domain_name},
            "RestApiId": {"Ref": f"{self.name}-rest-api"},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [f"{self.name}-domain"]
