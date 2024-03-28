from pareto2.services import hungarorise as H
from pareto2.services import AltNamespaceMixin

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
    However, when AllowCredentials is true, AllowOrigins cannot be '*'; it must specify actual origins rather than a wildcard for browsers to respect the AllowCredentials setting.
    """

    """
    In the context of an AWS API Gateway (especially for HTTP APIs, which your configuration suggests), including OPTIONS in the AllowedMethods of the CORS configuration is not necessary when you configure CORS directly through the API Gateway settings. AWS API Gateway automatically handles OPTIONS preflight requests for you when CORS is enabled at the API level. This simplification is part of the service's features to make CORS management easier.
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
                "AllowCredentials": False, # NB see above
                "ExposeHeaders": [
                    "X-Custom-Header"
                ],
                "MaxAge": 3600
            },
            "ProtocolType": "HTTP",
            "AutoDeploy": True
        }

    @property
    def visible(self):
        return True

class Route(AltNamespaceMixin, Resource):
    
    def __init__(self, namespace, api_namespace, endpoint):
        self.namespace = namespace
        self.api_namespace = api_namespace
        self.endpoint = endpoint

    @property
    def aws_properties(self):
        integration_ref =  H(f"{self.namespace}-integration")
        props = {
            "RouteKey": "%s %s%s" % (self.endpoint["method"],
                                     "" if self.endpoint["path"].startswith("/") else "/",
                                     self.endpoint["path"]),
            "Target": {"Fn::Sub": f"/aws/lambda/${{{integration_ref}}}"},
            "ApiId": {"Ref": H(f"{self.api_namespace}-api")}
        }
        if (self.endpoint["method"] == "GET" and
            "parameters" in self.endpoint):
            props["RequestParameters"] = {f"querystrings.{param}": {"Required": True}
                                          for param in self.endpoint["parameters"]}
        return props
        
class Integration(AltNamespaceMixin, Resource):
    
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
            "Audience": [{"Ref": H(f"{self.namespace}-user-pool-web-client")}] 
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
    
class ApiMapping(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": H("domain-name")},
            "ApiId": {"Ref": H(f"{self.namespace}-api")}
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-domain-name")]
