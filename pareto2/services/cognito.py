from pareto2.services import hungarorise as H
from pareto2.services import Resource

from pareto2.services.iam import *

class UserPool(Resource):

    @property
    def visible(self):
        return True

class SimpleEmailUserPool(UserPool):

    def __init__(self, namespace, attributes, **kwargs):
        super().__init__(namespace = namespace,
                         **kwargs)
        self.attributes = attributes
    
    """
    LambdaConfig binds to all relevant hooks; filter at event level by matching on event name
    """

    @property
    def lambda_config(self):
        custom_message_arn = {"Fn::GetAtt": [H(f"{self.namespace}-custom-message-function"), "Arn"]}
        lambda_config = {"CustomMessage": custom_message_arn}
        return lambda_config


    """
    If you have UsernameAttributes set to email but do not have UsernameConfiguration set, Cognito will allow users to sign in with their email address, but it will not guarantee that the userName property is set to the email. The userName field may still contain a UUID or another value assigned by Cognito.

    To ensure that the userName property is set to the email, you need to explicitly configure the UsernameConfiguration in your CloudFormation template.
    """

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
            "LambdaConfig": self.lambda_config,
            "Policies": {"PasswordPolicy": password_policy},
            "Schema": schema,
            "UsernameAttributes": ["email"],
            "UsernameConfiguration": {
                "CaseSensitive": False
            }
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

"""
- https://stackoverflow.com/a/46028801/124179
- https://chatgpt.com/c/9597be53-c249-438b-be81-9abba956c0c2
"""
        
class IdentityPoolAuthenticatedRole(IdentityPoolRoleBase):

    def __init__(self, namespace):
        super().__init__(namespace = f"{namespace}-identity-pool-authenticated",
                         condition = {
                             "StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
                             "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "authenticated"}
                         })

class IdentityPoolAuthenticatedPolicy(Policy):

    def __init__(self, namespace):
        super().__init__(namespace =  f"{namespace}-identity-pool-authenticated",
                         permissions = ["cognito-identity:GetId",
                                        "cognito-identity:GetCredentialsForIdentity",
                                        "cognito-identity:DescribeIdentity",
                                        "cognito-idp:ListUsers",
                                        "cognito-idp:ListGroups",
                                        "cognito-idp:AdminGetUser"])

class IdentityPoolUnauthenticatedRole(IdentityPoolRoleBase):

    def __init__(self, namespace):
        super().__init__(namespace = f"{namespace}-identity-pool-unauthenticated",
                         condition = {
                             "StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
                             "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "unauthenticated"}
                         })

class IdentityPoolUnauthenticatedPolicy(Policy):

    def __init__(self, namespace):
        super().__init__(namespace = f"{namespace}-identity-pool-unauthenticated",
                         permissions = ["cognito-identity:GetId",
                                        "cognito-identity:GetOpenIdToken"])
    
class IdentityPoolRoleAttachment(Resource):
    
    @property
    def aws_properties(self):
        identity_pool_id = {"Ref": H(f"{self.namespace}-identity-pool")}
        auth_role = {"Fn::GetAtt": [H(f"{self.namespace}-identity-pool-authenticated-role"), "Arn"]}
        unauth_role = {"Fn::GetAtt": [H(f"{self.namespace}-identity-pool-unauthenticated-role"), "Arn"]}
        roles = {
            "authenticated": auth_role,
            "unauthenticated": unauth_role
        }
        return {
            "Roles": roles,
            "IdentityPoolId": identity_pool_id
        }
    


