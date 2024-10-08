from pareto2.services import hungarorise as H
from pareto2.services import Resource

LambdaMethodArn = "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

class Api(Resource):

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
                    {"Ref": H("dev-ui-endpoint")},
                    {"Ref": H("prod-ui-endpoint")}
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
        super().__init__(namespace)
        self.stage_name = stage_name

    @property
    def aws_properties(self):
        return {
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "StageName": self.stage_name,
            "AutoDeploy": True
        }

class Route(Resource):
    
    def __init__(self, namespace, api_namespace, endpoint):
        super().__init__(namespace)
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
        super().__init__(namespace)
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

    """
    APIGateway v2 works with RegionalDomainName/RegionalHostedZoneId; you don't have to use DistributionDomainName/DistributionHostedZoneId (in fact I don't believe these are supported by AWS::APiGatewayV2::DomainName)
    There is no us-east-1 requirement, nor Cloudfront dependency
    """
    
    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "DomainNameConfigurations": [
                {"CertificateArn": {"Ref": H("regional-certificate-arn")}}
            ]
        }

class ApiMapping(Resource):

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "ApiId": {"Ref": H(f"{self.namespace}-api")},
            "Stage": {"Ref": H(f"{self.namespace}-stage")}
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-domain-name")]

