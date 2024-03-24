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

class Route(AltNamespaceMixin, Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

class Integration(AltNamespaceMixin, Resource):
    
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
    
class ApiMapping(Resource):

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
