class UserPool:

    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-user-pool"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::UserPool"

    """
    password policy, schema should be part of component
    """
    
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
    
    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-user-pool-client"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::UserPoolClient"

    @property
    def aws_properties(self):
        return {
            "UserPoolId": {"Ref": f"{self.name}-user-pool"},
            "PreventUserExistenceErrors": "ENABLED",
            "ExplicitAuthFlows": self.explicit_auth_flows
        }

class IdentityPoolBase:

    def __init__(self, name, client_id):
        self.name = name
        self.client_id = client_id

    @property
    def resource_name(self):
        return f"{self.name}-identity-pool"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::IdentityPool"

    @property
    def aws_properties(self):
        client_id = {"Ref": self.client_id}
        provider_name = {"Fn::GetAtt": [f"{self.name}-user-pool", "ProviderName"]}
        provider = {"ClientId": client_id,
                    "ProviderName": provider_name}
        return {
            "AllowUnauthenticatedIdentities": True,
            "CognitoIdentityProviders": [provider]
        }

class IdentityPoolRoleAttachment:
    
    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-identity-pool-role-attachment"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::IdentityPoolRoleAttachment"

    @property
    def aws_properties(self):
        identity_pool_id = {"Ref": f"{self.name}-identity-pool"}
        auth_role = {"Fn::GetAtt": [f"{self.name}-identity-pool-authorized-role", "Arn"]}
        unauth_role = {"Fn::GetAtt": [f"{self.name}-identity-pool-unauthorized-role", "Arn"]}
        roles = {
            "authenticated": auth_role,
            "unauthenticated": unauth_role
        }
        return {
            "Roles": roles,
            "IdentityPoolId": identity_pool_id
        }
    

