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

    @property
    def aws_properties(self):
        raise NotImplementedError("Subclasses must implement aws_properties")

    @property
    def depends(self):
        raise NotImplementedError("Subclasses must implement depends")

class Stage:

    def __init__(self, name, stage_name, deployment_id_ref, rest_api_id_ref):
        self.name = name
        self.stage_name = stage_name
        self.deployment_id_ref = deployment_id_ref
        self.rest_api_id_ref = rest_api_id_ref

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
            "DeploymentId": {"Ref": self.deployment_id_ref},
            "RestApiId": {"Ref": self.rest_api_id_ref}
        }
    
class Resource:

    def __init__(self, name, rest_api_ref, pathpart, parent_id_ref="RootResourceId"):
        self.name = name
        self.rest_api_ref = rest_api_ref
        self.pathpart = pathpart
        self.parent_id_ref = parent_id_ref

    @property
    def resource_name(self):
        return f"{self.name}-resource"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Resource"

    @property
    def aws_properties(self):
        parent_id = {"Fn::GetAtt": [self.rest_api_ref, self.parent_id_ref]}
        return {
            "ParentId": parent_id,
            "PathPart": self.pathpart,
            "RestApiId": {"Ref": self.rest_api_ref}
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

    @property
    def aws_properties(self):
        raise NotImplementedError("Subclasses must implement this property.")

class Authorizer:
    
    def __init__(self, name, rest_api_id_ref, authorizer_type, identity_source):
        self.name = name
        self.rest_api_id_ref = rest_api_id_ref
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
            "RestApiId": {"Ref": self.rest_api_id_ref},
            "Type": self.authorizer_type
        }

    

class DomainName:

    def __init__(self, name, domain_name_ref="domain-name", certificate_arn_ref="certificate-arn"):
        self.name = name
        self.domain_name_ref = domain_name_ref
        self.certificate_arn_ref = certificate_arn_ref

    @property
    def resource_name(self):
        return f"{self.name}-domain"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::DomainName"

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": self.domain_name_ref},
            "CertificateArn": {"Ref": self.certificate_arn_ref}
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
