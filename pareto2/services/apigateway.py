from pareto2.services import hungarorise as H
from pareto2.services import Resource as AWSResource # distinguish between aws.Resource and apigw.Resource

class RestApi(AWSResource):

    def __init__(self, namespace):
        super().__init__(namespace)

    """
    - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-restapi.html
    - The name of the RestApi. A name is required if the REST API is not based on an OpenAPI specification
    - generally a good idea to include AWS::StackName in case Name exists in a global namespace
    """
        
    @property
    def aws_properties(self):
        return  {
            "Name": {"Fn::Sub": f"{self.namespace}-rest-api-${{AWS::StackName}}"},
            "BinaryMediaTypes": ["*/*"]
        }

    @property
    def visible(self):
        return True

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-deployment.html
- Deployment has a StageName property, but Cloudformation complains if you try and use it ("stage already created")
"""
    
class Deployment(AWSResource):

    def __init__(self, namespace, methods):
        super().__init__(namespace)
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

    def __init__(self, namespace, stage_name = "prod"):
        super().__init__(namespace)
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
        super().__init__(namespace)
        self.path = path

    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.namespace}-rest-api"), "RootResourceId"]},
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}
        }

class Method(AWSResource):
    
    pass
    
class DomainName(AWSResource):
    
    """
    APIGateway v1 requires DistributionDomainName/DistributionHostedZoneId (not Regional) 
    Certificate must be in us-east-1 and there is a (hidden) Cloudfront dependency
    """
    
    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "CertificateArn": {"Ref": H("distribution-certificate-arn")}
        }
    
class BasePathMapping(AWSResource):

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")},
            "Stage": {"Ref": H(f"{self.namespace}-stage")}
        }

