from pareto.aws.apigateway import *
from pareto.aws.cognito import *
from pareto.aws.iam import Role as RoleBase
from pareto.aws.lambda import Permission as PermissionsBase
from pareto.aws.route53 import *

class Permission(PermissionBase):
    
    def __init__(self, api, endpoint):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{api['name']}/{endpoint['method']}/{endpoint['path']}"}
        super().__init__(endpoint["name"],
                         endpoint["action"],
                         source_arn,
                         "apigateway.amazonaws.com")        
            
class IdentityPoolUnauthorizedRole(RoleBase):

    def __init__(self, name):
        RoleBase.__init__(self,
                          name=f"{name}-identity-pool-unauthorized",
                          permissions=["mobileanalytics:PutEvents",
                                       "cognito-sync:*"])
        
class IdentityPoolAuthorizedRole(RoleBase):

    def __init__(self):
        RoleBase.__init__(self,
                          name=f"{name}-identity-pool-authorized",
                          permissions or ["mobileanalytics:PutEvents",
                                         "cognito-sync:*",
                                         "cognito-identity:*",
                                         "lambda:InvokeFunction"])
