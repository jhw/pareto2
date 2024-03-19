from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import Resource, AltNamespaceMixin
from pareto2.ingredients.iam import Role

class UserPool(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def visible(self):
        return True

class SimpleEmailUserPool(UserPool):

    def  __init__(self, namespace):
        super().__init__(namespace = namespace)
        
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

class UserPoolClient(AltNamespaceMixin, Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "UserPoolId": {"Ref": H(f"{self.namespace}-user-pool")},
            "PreventUserExistenceErrors": "ENABLED",
            "ExplicitAuthFlows": self.explicit_auth_flows
        }

    @property
    def visible(self):
        return True

class UserPoolAdminClient(UserPoolClient):

    def __init__(self, namespace):
        super().__init__(namespace = namespace)

    @property
    def explicit_auth_flows(self):
        return [
            "ALLOW_ADMIN_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ]

class UserPoolWebClient(UserPoolClient):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace)

    @property
    def explicit_auth_flows(self):
        return [
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ]        
    
class IdentityPool(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        client_id = {"Ref": H(f"{self.namespace}-user-pool-web-client")}
        provider_name = {"Fn::GetAtt": [H(f"{self.namespace}-user-pool"), "ProviderName"]}
        provider = {"ClientId": client_id,
                    "ProviderName": provider_name}
        return {
            "AllowUnauthenticatedIdentities": True,
            "CognitoIdentityProviders": [provider]
        }

    @property
    def visible(self):
        return True

def identity_pool_role_condition(namespace, typestr):
    return {"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
            "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
    
class IdentityPoolAuthorizedRole(AltNamespaceMixin, Role):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         action = "sts:AssumeRoleWithWebIdentity",
                         condition = identity_pool_role_condition(namespace, typestr = "authorized"),
                         principal = {"Federated": "cognito-identity.amazonaws.com"},
                         permissions = ["cognito-sync:*",
                                        "cognito-identity:*",
                                        "lambda:InvokeFunction"])

class IdentityPoolUnauthorizedRole(AltNamespaceMixin, Role):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         action = "sts:AssumeRoleWithWebIdentity",
                         condition = identity_pool_role_condition(namespace, typestr = "unauthorized"),
                         principal = {"Federated": "cognito-identity.amazonaws.com"},
                         permissions = ["cognito-sync:*"])
    
class IdentityPoolRoleAttachment(Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

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
    

