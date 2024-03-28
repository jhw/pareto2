from pareto2.services import hungarorise as H

from pareto2.services import Resource

LambdaMethodArn = "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

class Api(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    """
    - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigatewayv2-api.html#cfn-apigatewayv2-api-name
    - Name: The name of the API. Required unless you specify an OpenAPI definition for Body or S3BodyLocation.
    """

    """
    AllowCredentials needs to be True, and you can't use wildcards for AllowOrigins :/

    - https://stackoverflow.com/questions/35190615/api-gateway-cors-no-access-control-allow-origin-header
    - https://stackoverflow.com/a/43029002/124179
    """
    
    @property
    def aws_properties(self):
        return {
            "Name": {"Fn::Sub": f"{self.namespace}-api-${{AWS::StackName}}"},
            "CorsConfiguration": {
                "AllowOrigins": [
                    "*"
                ],
                "AllowMethods": [
                    "GET",
                    "POST"
                ],
                "AllowHeaders": [
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key"
                ],
                "AllowCredentials": True,
                "ExposeHeaders": [
                    "X-Custom-Header"
                ],
                "MaxAge": 3600
            },
            "ProtocolType": "HTTP"
        }

    @property
    def visible(self):
        return True

class Stage(Resource):

    def __init__(self, namespace, stage_name = "prod"):
        self.namespace = namespace
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "StageName": self.stage_name,
            "AutoDeploy": True
        }

    @property
    def visible(self):
        return True
        
class Route(Resource):
    
    def __init__(self, namespace, api_namespace, endpoint):
        self.namespace = namespace
        self.api_namespace = api_namespace
        self.endpoint = endpoint

    @property
    def aws_properties(self):
        integration_ref =  H(f"{self.namespace}-integration")
        return {
            "RouteKey": "%s %s%s" % (self.endpoint["method"],
                                     "" if self.endpoint["path"].startswith("/") else "/",
                                     self.endpoint["path"]),
            "Target": {"Fn::Sub": f"integrations/${{{integration_ref}}}"},
            "ApiId": {"Ref": H(f"{self.api_namespace}-api")}
        }
        
class Integration(Resource):
    
    def __init__(self, namespace, api_namespace):
        self.namespace = namespace
        self.api_namespace = api_namespace

    @property
    def aws_properties(self):
        integration_uri = {"Fn::Sub": [LambdaMethodArn, {"arn": {"Fn::GetAtt": [H(f"{self.namespace}-function"), "Arn"]}}]}
        return {
            "ApiId": {"Ref": H(f"{self.api_namespace}-api")},
            "IntegrationType": "AWS_PROXY",
            "IntegrationUri": integration_uri,
            "PayloadFormatVersion": "2.0",
            "IntegrationMethod": "POST"            
        }
        
class Authorizer(Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

    """
    - https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigatewayv2-authorizer.html#cfn-apigatewayv2-authorizer-name
    - Name: The name of the authorizer; Required: Yes
    """
 
    @property
    def aws_properties(self):
        user_pool_ref =  H(f"{self.namespace}-user-pool")
        issuer = {"Fn::Sub": f"https://cognito-idp.${{AWS::Region}}.amazonaws.com/${{{user_pool_ref}}}"}        
        jwt_config = {
            "Issuer": issuer,
            "Audience": [{"Ref": H(f"{self.namespace}-user-pool-client")}] 
        }
        return {
            "AuthorizerType": "JWT",
            "JwtConfiguration": jwt_config,
            "IdentitySource": ["$request.header.Authorization"],
            "Name": {"Fn::Sub": f"{self.namespace}-authorizer-${{AWS::StackName}}"},
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
        }

class DomainName(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "DomainNameConfigurations": [
                {"CertificateArn": {"Ref": H("certificate-arn")}}
            ]
        }

"""
- ApiMapping used to depend on DomainName but have removed it to see what happens
"""
    
class ApiMapping(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "Stage": {"Ref": H(f"{self.namespace}-stage")}
        }

