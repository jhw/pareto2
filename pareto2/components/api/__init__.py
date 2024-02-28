# Subclass for IdentityPool Unauthorized Role
class IdentityPoolUnauthorizedRole(FunctionBase):
    def __init__(self, api, permissions=None):
        super().__init__(api["name"], permissions or ["mobileanalytics:PutEvents", "cognito-sync:*"])

# Subclass for IdentityPool Authorized Role
class IdentityPoolAuthorizedRole(FunctionBase):
    def __init__(self, api, permissions=None):
        super().__init__(api["name"], permissions or ["mobileanalytics:PutEvents", "cognito-sync:*", "cognito-identity:*", "lambda:InvokeFunction"])

