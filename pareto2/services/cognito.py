from pareto2.services import hungarorise as H
from pareto2.services import Resource

from pareto2.services.iam import *

class UserPool(Resource):

    @property
    def visible(self):
        return True

class SimpleEmailUserPool(UserPool):

    @property    
    def aws_properties(self, nmin = 8):
        password_policy = {
            "MinimumLength": nmin,
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
    
    @property
    def aws_properties(self):
        return {
            "UserPoolId": {"Ref": H(f"{self.namespace}-user-pool")},
            "PreventUserExistenceErrors": "ENABLED",
            "ExplicitAuthFlows": [
                "ALLOW_USER_SRP_AUTH", # for web access
                "ALLOW_ADMIN_USER_PASSWORD_AUTH", # for localhost testing
                "ALLOW_REFRESH_TOKEN_AUTH"
            ]
        }

    @property
    def visible(self):
        return True

"""
You should be able to use a User pool without an Identity pool, but experience of the Flutter Amplify libraries suggests an Identity pool is always required, even if not used

All this Identity pool code is therefore boilerplate; not really clear if it should live in services or recipes; for now, keep it in the former

Could set AllowUnauthenticatedIdentities to False, but don't know precisely what Amplify Auth requires from IdentityPool
"""

class IdentityPool(Resource):

    @property
    def aws_properties(self):
        client_id = {"Ref": H(f"{self.namespace}-user-pool-client")}
        provider_name = {"Fn::GetAtt": [H(f"{self.namespace}-user-pool"), "ProviderName"]}
        provider = {"ClientId": client_id,
                    "ProviderName": provider_name}
        return {
            "AllowUnauthenticatedIdentities": True, # NB
            "CognitoIdentityProviders": [provider]
        }

    @property
    def visible(self):
        return True

class IdentityPoolRoleBase(Role):

    def __init__(self, namespace, **kwargs):
        super().__init__(namespace = namespace,
                         action = "sts:AssumeRoleWithWebIdentity",
                         principal =  {"Federated": "cognito-identity.amazonaws.com"},                       
                         **kwargs)

class IdentityPoolAuthorizedRole(IdentityPoolRoleBase):

    def __init__(self, namespace):
        super().__init__(namespace = f"{namespace}-identity-pool-authorized",
                         condition = {
                             "StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
                             "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "authorized"}
                         })

class IdentityPoolAuthorizedPolicy(Policy):

    def __init__(self, namespace):
        super().__init__(namespace =  f"{namespace}-identity-pool-authorized",
                         permissions = ["cognito-sync:*",
                                        "cognito-identity:*",
                                        "lambda:InvokeFunction"])

class IdentityPoolUnauthorizedRole(IdentityPoolRoleBase):

    def __init__(self, namespace):
        super().__init__(namespace = f"{namespace}-identity-pool-unauthorized",
                         condition = {
                             "StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
                             "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "unauthorized"}
                         })

class IdentityPoolUnauthorizedPolicy(Policy):

    def __init__(self, namespace):
        super().__init__(namespace = f"{namespace}-identity-pool-unauthorized",
                         permissions = ["cognito-sync:*"])
    
class IdentityPoolRoleAttachment(Resource):
    
    @property
    def aws_properties(self):
        identity_pool_id = {"Ref": H(f"{self.namespace}-identity-pool")}
        auth_role = {"Fn::GetAtt": [H(f"{self.namespace}-identity-pool-authorized-role"), "Arn"]}
        unauth_role = {"Fn::GetAtt": [H(f"{self.namespace}-identity-pool-unauthorized-role"), "Arn"]}
        roles = {
            "authenticated": auth_role,
            "unauthenticated": unauth_role
        }
        return {
            "Roles": roles,
            "IdentityPoolId": identity_pool_id
        }
    

