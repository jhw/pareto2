class UserPool:

    def __init__(self, api):
        self.api = api

    @property
    def resource_name(self):
        return f"{self.api['name']}-api-userpool"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::UserPool"

    @property
    def aws_properties(self):
        password_policy = {
            "MinimumLength": 8,
            "RequireLowercase": True,
            "RequireNumbers": True,
            "RequireSymbols": True,
            "RequireUppercase": True
        }
        schema = [{
            "AttributeDataType": "String",
            "Mutable": True,
            "Name": "email",
            "Required": True,
            "StringAttributeConstraints": {"MinLength": "1"}
        }]
        return {
            "AutoVerifiedAttributes": ["email"],
            "Policies": {"PasswordPolicy": password_policy},
            "Schema": schema,
            "UsernameAttributes": ["email"]
        }

class UserPoolClient:
    
    def __init__(self, api, client_type):
        self.api = api
        self.client_type = client_type

    @property
    def resource_name(self):
        return f"{self.api['name']}-api-userpool-{self.client_type}-client"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::UserPoolClient"

    @property
    def aws_properties(self):
        return {
            "UserPoolId": {"Ref": f"{self.api['name']}-api-userpool"},
            "PreventUserExistenceErrors": "ENABLED",
            "ExplicitAuthFlows": self.explicit_auth_flows
        }

    @property
    def explicit_auth_flows(self):
        raise
    
class IdentityPoolBase:

    def __init__(self, api):
        self.api = api

    @property
    def resource_name(self):
        return f"{self.api['name']}-api-identitypool"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::IdentityPool"

    @property
    def aws_properties(self):
        client_id = {"Ref": f"{self.api['name']}-api-userpool-web-client"}
        provider_name = {"Fn::GetAtt": [f"{self.api['name']}-api-userpool", "ProviderName"]}
        provider = {"ClientId": client_id, "ProviderName": provider_name}
        return {
            "AllowUnauthenticatedIdentities": True,
            "CognitoIdentityProviders": [provider]
        }

class IdentityPoolRoleAttachment:
    
    def __init__(self, api):
        self.api = api

    @property
    def resource_name(self):
        return f"{self.api['name']}-api-identitypool-mapping"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::IdentityPoolRoleAttachment"

    @property
    def aws_properties(self):
        identity_pool_id = {"Ref": f"{self.api['name']}-api-identitypool"}
        auth_role = {"Fn::GetAtt": [f"{self.api['name']}-api-identitypool-authorized-role", "Arn"]}
        unauth_role = {"Fn::GetAtt": [f"{self.api['name']}-api-identitypool-unauthorized-role", "Arn"]}
        roles = {
            "authenticated": auth_role,
            "unauthenticated": unauth_role
        }
        return {
            "Roles": roles,
            "IdentityPoolId": identity_pool_id
        }
    

