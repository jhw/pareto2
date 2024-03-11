from pareto2.aws import hungarorise as H
from pareto2.aws import Resource, dehungarorise

class UserPool(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def visible(self):
        return True

class SimpleEmailUserPool(UserPool):

    def  __init__(self, namespace):
        super().__init__(namespace)
        
    @property    
    def aws_properties(self, nmin=8):
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

    """
    - when you subclass a resource and need to reference it from other resources in the same module, it's simplest to override the resource_name parameter so it refers to the base class rather than the current subclass
    - this way other resources in the same module can refence this resource using the standard aws resource name rather than the subclass name
    - where the subclass is not referenced by other resources in the module (but is referenced at the component level - eg endpoint stuff, gateway responses) it's more convenient to have the subclass type as part of the resource name
    """
    
    @property
    def resource_name(self):    
        tokens=self.class_names[-2].split(".") # base class not subclass
        return "%s-%s" % (self.namespace, dehungarorise(tokens[-1]))


class UserPoolClient(Resource):
    
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
        super().__init__(namespace)

    @property
    def explicit_auth_flows(self):
        return [
            "ALLOW_ADMIN_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ]

class UserPoolWebClient(UserPoolClient):
    
    def __init__(self, namespace):
        super().__init__(namespace)

    @property
    def explicit_auth_flows(self):
        return [
            "ALLOW_USER_SRP_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH"
        ]        
    
class IdentityPool(Resource):

    def __init__(self, namespace, client_id):
        self.namespace = namespace
        self.client_id = client_id

    @property
    def aws_properties(self):
        client_id = {"Ref": self.client_id}
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
    

