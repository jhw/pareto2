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

