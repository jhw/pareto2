from pareto.aws.apigateway import *
from pareto.aws.cognito import *
from pareto.aws.iam import Role as RoleBase
from pareto.aws.lambda import Permission as PermissionsBase
from pareto.aws.route53 import *

class Permission(PermissionBase):
    
    def __init__(self, name, function_name, method, path):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{name}/{method}/{path}"}
        PermissionBase.__init__(self, name,
                                function_name,
                                source_arn,
                                "apigateway.amazonaws.com")

class IdentityPoolRole(RoleBase):

    def __init__(self, name, permissions):
        Role.__init__(self, name, permissions)
    
    def policy_document(self, typestr):
        condition={"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{self.name}-identity-pool")}},
                   "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
        statement=[{"Effect": "Allow",
                    "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                    "Action": ["sts:AssumeRoleWithWebIdentity"],
                    "Condition": condition}]
        return {"Version": "2012-10-17",
                "Statement": statement}
        
class IdentityPoolUnauthorizedRole(IdentityPoolRole):

    def __init__(self, name):
        IdentityPoolRole.__init__(self,
                                  name=f"{name}-identity-pool-unauthorized",
                                  permissions=["mobileanalytics:PutEvents",
                                               "cognito-sync:*"])

    @property
    def policy_document(self):
        return IdentityPoolRole.policy_document(self, "unauthorized")
        
class IdentityPoolAuthorizedRole(IdentityPoolRole):

    def __init__(self):
        IdentityPoolRole.__init__(self,
                                  name=f"{name}-identity-pool-authorized",
                                  permissions or ["mobileanalytics:PutEvents",
                                                  "cognito-sync:*",
                                                  "cognito-identity:*",
                                                  "lambda:InvokeFunction"])
    @property
    def policy_document(self):
        return IdentityPoolRole.policy_document(self, "authorized")
