from pareto2.services import hungarorise as H
from pareto2.services import AltNamespaceMixin

from pareto2.services import Resource

StageName = "prod"

class Api(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "Name": {"Fn::Sub": f"{self.namespace}-api-${{AWS::StackName}}"}
        }

    @property
    def visible(self):
        return True

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-deployment.html
- Deployment has a StageName property, but Cloudformation complains if you try and use it ("stage already created")
"""
    
class Deployment(Resource):

    def __init__(self, namespace, methods):
        self.namespace = namespace
        self.methods = methods

    @property
    def aws_properties(self):
        return {
            "ApiId": {"Ref": H(f"{self.namespace}-api")}
        }

    @property
    def depends(self):
        return self.methods
                
class Stage(Resource):

    def __init__(self, namespace, stage_name = StageName):
        self.namespace = namespace
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "StageName": self.stage_name,
            "DeploymentId": {"Ref": H(f"{self.namespace}-deployment")},
            "ApiId": {"Ref": H(f"{self.namespace}-api")}
        }

class Method(AltNamespaceMixin, Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

class Authorizer(Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

    """
    - feels like all APIGW authentication is going to be done against a UserPool, so it's okay to make this Cognito- centric in a base class
    """
        
    @property
    def aws_properties(self):
        return {
            "ProviderARNs": [{"Fn::GetAtt": [H(f"{self.namespace}-user-pool"), "Arn"]}],
            "IdentitySource": "method.request.header.Authorization",
            "Name": {"Fn::Sub": f"{self.namespace}-authorizer-${{AWS::StackName}}"},
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "Type": "COGNITO_USER_POOLS"
        }

class RequestValidator(AltNamespaceMixin, Resource):

    def __init__(self, namespace, parent_namespace, validate_request_parameters = False, validate_request_body = False):
        self.namespace = namespace
        self.parent_namespace = parent_namespace
        self.validate_request_parameters = validate_request_parameters
        self.validate_request_body = validate_request_body

    @property
    def aws_properties(self):
        return {"ApiId": {"Ref": H(f"{self.parent_namespace}-api")},
                "ValidateRequestParameters": self.validate_request_parameters,
                "ValidateRequestBody": self.validate_request_body}

class ParameterRequestValidator(RequestValidator):

    def __init__(self, namespace, parent_namespace):
        return super().__init__(namespace = namespace,
                                parent_namespace = parent_namespace,
                                validate_request_parameters = True)

class SchemaRequestValidator(RequestValidator):

    def __init__(self, namespace, parent_namespace):
        return super().__init__(namespace = namespace,
                                parent_namespace = parent_namespace,
                                validate_request_body = True)

"""
- a Model only gets called if the request contains a ContentType header which matches one of the entries in the RequestModels attribute of the connected Method
- else everything will be waived through by the AWS_PROXY integration method type :/
"""
    
class Model(Resource):
    
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
    - docs say Name is not required, but experiments suggest it is very much required, and must be alphanumeric is no punctuation
    - hence hungarorised resource name probably the best option; don't include ${AWS::StackName} as can't be sure that the format is valid for Name 
    """
        
    @property
    def aws_properties(self):
        return {
            "ApiId": {"Ref": H(f"{self.parent_namespace}-api")},
            "ContentType": self.content_type,
            "Name": H(f"{self.namespace}-model"),
            "Schema": self.schema
        }

class GatewayResponse(AltNamespaceMixin, Resource):

    def __init__(self, namespace, response_type):
        self.namespace = namespace
        self.response_type = response_type

    @property
    def aws_properties(self):
        response_parameters = {"gatewayresponse.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                      for k, v in [("headers", "*"),
                                   ("origin", "*")]}
        return {
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "ResponseType": f"DEFAULT_{self.response_type}",
            "ResponseParameters": response_parameters
        }
    
class GatewayResponse4xx(GatewayResponse):

    def __init__(self, namespace):
        return super().__init__(namespace = namespace,
                                response_type = "4XX")

class GatewayResponse5xx(GatewayResponse):

    def __init__(self, namespace):
        return super().__init__(namespace = namespace,
                                response_type = "5XX")
        
class DomainName(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "CertificateArn": {"Ref": H("certificate-arn")}
        }
    
class BasePathMapping(Resource):

    def __init__(self, namespace, stage_name = StageName):
        self.namespace = namespace
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-domain-name")]
