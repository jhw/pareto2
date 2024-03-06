from pareto2.aws.apigateway import Authorizer as AuthorizerBase
from pareto2.aws.apigateway import BasePathMapping as BasePathMappingBase
from pareto2.aws.apigateway import Deployment as DeploymentBase
from pareto2.aws.apigateway import DomainName as DomainNameBase
from pareto2.aws.apigateway import GatewayResponse as GatewayResponseBase
from pareto2.aws.apigateway import Method as MethodBase
from pareto2.aws.apigateway import Model as ModelBase
from pareto2.aws.apigateway import RequestValidator as RequestValidatorBase
from pareto2.aws.apigateway import Resource as ResourceBase
from pareto2.aws.apigateway import RestApi as RestApiBase
from pareto2.aws.apigateway import Stage as StageBase

from pareto2.aws.cognito import IdentityPool as IdentityPoolBase
from pareto2.aws.cognito import IdentityPoolRoleAttachment as IdentityPoolRoleAttachmentBase
from pareto2.aws.cognito import UserPool as UserPoolBase
from pareto2.aws.cognito import UserPoolClient as UserPoolClientBase

from pareto2.aws.iam import Role as RoleBase

from pareto2.aws.lambda import Permission as PermissionBase

from pareto2.aws.route53 import RecordSet as RecordSetBase

### core

class RestApi(RestApiBase):

    def __init__(self, api):
        super().__init__(api["name"])

class Stage(StageBase):
    
    def __init__(self, api):
        super().__init__(api["name"], api["stage"]["name"], f"{api['name']}-api-deployment", f"{api['name']}-api-rest-api")
    
"""
- NB includes method and cors method
"""
        
class Deployment(DeploymentBase):

    def __init__(self, api):
        super().__init__(api["name"])
        self.api = api

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": f"{self.name}-api-rest-api"}
        }

    @property
    def depends(self):
        dependencies = []
        for endpoint in self.api["endpoints"]:
            dependencies += [f"{endpoint['name']}-api-method",
                             f"{endpoint['name']}-api-cors-method"]
        return dependencies
        
class Resource(ResourceBase):

    def __init__(self, api, endpoint):
        super().__init__(endpoint["name"], f"{api['name']}-api-rest-api", endpoint["path"])

class Permission(PermissionBase):
    
    def __init__(self, api, endpoint):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{api['name']}/{endpoint['method']}/{endpoint['path']}"}
        super().__init__(endpoint["name"],
                         endpoint["action"],
                         source_arn,
                         "apigateway.amazonaws.com")
        
### validation
        
class RequestValidator(RequestValidatorBase):

    def __init__(self, api, endpoint):
        super().__init__(api["name"], f"{api['name']}-api-rest-api")
        self.endpoint = endpoint

    def validation_settings(self):
        settings = {}
        if "parameters" in self.endpoint:
            settings["ValidateRequestParameters"] = True
        if "schema" in self.endpoint:
            settings["ValidateRequestBody"] = True
        return settings

class Model(ModelBase):

    def __init__(self, api, endpoint, schematype="http://json-schema.org/draft-04/schema#"):
        super().__init__(api["name"], f"{api['name']}-api-rest-api", f"{endpoint['name']}-api-model")
        self.endpoint = endpoint
        self.schematype = schematype

    def schema(self):
        schema = self.endpoint.get("schema", {})
        if "$schema" not in schema:
            schema["$schema"] = self.schematype
        return schema
    
### CORS

class CorsMethod(MethodBase):
    
    def __init__(self, api, endpoint, **kwargs):
        super().__init__(endpoint["name"], **kwargs)
        self.api = api
        self.endpoint = endpoint

    @property
    def aws_properties(self):
        def init_integration_response(endpoint):
            params = {k.capitalize(): "'%s'" % v for k, v in [
                ("headers", ",".join(["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"])),
                ("methods", f"{endpoint['method']},OPTIONS"),
                ("origin", "*")
            ]}
            templates = {"application/json": ""}
            return {"StatusCode": 200, "ResponseParameters": params, "ResponseTemplates": templates}

        integration_response = init_integration_response(self.endpoint)
        integration

"""
- needs separate subclasses for 400, 500 responses
"""
    
class CorsGatewayResponse(GatewayResponseBase):

    def __init__(self, api, code):
        super().__init__(api["name"], f"DEFAULT_{code}", f"{api['name']}-api-rest-api")
        self.code = code

    def response_parameters(self):
        cors_headers = {
            "Access-Control-Allow-Headers": "'*'",
            "Access-Control-Allow-Origin": "'*'"
        }
        # Format the parameters to match the AWS::ApiGateway::GatewayResponse format
        params = {f"gatewayresponse.header.{k}": v for k, v in cors_headers.items()}
        return params
        
### domain
        
class DomainName(DomainNameBase):

    def __init__(self, api):
        super().__init__(api["name"])

class BasePathMapping(BasePathMappingBase):

    def __init__(self, api):
        super().__init__(api["name"], "domain-name", api["stage"]["name"])
        self.api = api

class RecordSet(RecordSetBase):

    def __init__(self, api):
        super().__init__(api["name"], "api")
        
### auth

class Authorizer(AuthorizerBase):
    
    def __init__(self, api, user_pool_arn_ref):
        super().__init__(api["name"], f"{api['name']}-api-rest-api", "COGNITO_USER_POOLS", "method.request.header.Authorization")
        self.user_pool_arn_ref = user_pool_arn_ref

    @property
    def aws_properties(self):
        base_properties = super().aws_properties
        base_properties["ProviderARNs"] = [{"Fn::GetAtt": [self.user_pool_arn_ref, "Arn"]}]
        return base_properties    

class UserPool(UserPoolBase):
    
    def __init__(self, api):
        super().__init__(api)

class UserPoolAdminClient(UserPoolClientBase):

    def __init__(self, api):
        super().__init__(api, "admin")

    @property
    def explicit_auth_flows(self):
        return [
            "ALLOW_ADMIN_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ]

class UserPoolWebClient(UserPoolClientBase):
    
    def __init__(self, api):
        super().__init__(api, "web")

    @property
    def explicit_auth_flows(self):
        return [
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ]        

class IdentityPool(IdentityPoolBase):

    def __init__(self, api):
        super().__init__(api)

class IdentityPoolRoleAttachment(IdentityPoolRoleAttachmentBase):

    def __init__(self, api):
        super().__init__(api)
        
class IdentityPoolUnauthorizedRole(RoleBase):

    def __init__(self, api, permissions=None):
        super().__init__(api["name"],
                         permissions or ["mobileanalytics:PutEvents",
                                         "cognito-sync:*"])
        
class IdentityPoolAuthorizedRole(RoleBase):

    def __init__(self, api, permissions=None):
        super().__init__(api["name"],
                         permissions or ["mobileanalytics:PutEvents",
                                         "cognito-sync:*",
                                         "cognito-identity:*",
                                         "lambda:InvokeFunction"])
