from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class UserPool(Resource):

    def __init__(self, component_name):
        self.component_name = component_name

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

class UserPoolClient(Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        return {
            "UserPoolId": {"Ref": H(f"{self.component_name}-user-pool")},
            "PreventUserExistenceErrors": "ENABLED",
            "ExplicitAuthFlows": self.explicit_auth_flows
        }

class IdentityPool(Resource):

    def __init__(self, component_name, client_id):
        self.component_name = component_name
        self.client_id = client_id

    @property
    def aws_properties(self):
        client_id = {"Ref": self.client_id}
        provider_name = {"Fn::GetAtt": [H(f"{self.component_name}-user-pool"), "ProviderName"]}
        provider = {"ClientId": client_id,
                    "ProviderName": provider_name}
        return {
            "AllowUnauthenticatedIdentities": True,
            "CognitoIdentityProviders": [provider]
        }

class IdentityPoolRoleAttachment(Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        identity_pool_id = {"Ref": H(f"{self.component_name}-identity-pool")}
        auth_role = {"Fn::GetAtt": [H(f"{self.component_name}-identity-pool-authorized-role"), "Arn"]}
        unauth_role = {"Fn::GetAtt": [H(f"{self.component_name}-identity-pool-unauthorized-role"), "Arn"]}
        roles = {
            "authenticated": auth_role,
            "unauthenticated": unauth_role
        }
        return {
            "Roles": roles,
            "IdentityPoolId": identity_pool_id
        }
    
