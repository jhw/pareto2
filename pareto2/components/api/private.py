from pareto2.aws.iam import Role as RoleBase

class IdentityPoolRole(RoleBase):

    def __init__(self, name, permissions):
        super().__init__(name, permissions)
    
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
        super().__init__(name=f"{name}-identity-pool-unauthorized",
                         permissions=["mobileanalytics:PutEvents",
                                      "cognito-sync:*"])
        
    @property
    def policy_document(self):
        return IdentityPoolRole.policy_document(self, "unauthorized")
        
class IdentityPoolAuthorizedRole(IdentityPoolRole):

    def __init__(self):
        super().__init__(name=f"{name}-identity-pool-authorized",
                         permissions=["mobileanalytics:PutEvents",
                                      "cognito-sync:*",
                                      "cognito-identity:*",
                                      "lambda:InvokeFunction"])
    @property
    def policy_document(self):
        return IdentityPoolRole.policy_document(self, "authorized")

