from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as APIGWResource
from pareto2.aws.cognito import *
from pareto2.aws.iam import Role as RoleBase

# from pareto2.aws.lambda import Permission as PermissionsBase

import importlib
lambda_module = importlib.import_module("pareto2.aws.lambda")
PermissionBase = lambda_module.Permission

from pareto2.aws.route53 import *

from pareto2.components import Component

class Permission(PermissionBase):
    
    def __init__(self, name, function_name, method, path):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{name}/{method}/{path}"}
        super().__init__(name=name,
                         function_name=function_name,
                         source_arn=source_arn,
                         principal="apigateway.amazonaws.com")

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

"""
- Resource
- LambdaProxyMethod
- CorsMethod
- Permission
- Validator
- Model [post]
"""

class ApiBase(Component):

    def init_GET_endpoint(self, endpoint):
        return [APIGWResource(name=self.name,
                              path=endpoint["path"]),
                LambdaProxyMethod(name=self.name,
                                  function_name="whatevs",
                                  method=endpoint["method"],
                                  parameters=endpoint["parameters"])]

class PublicApi(ApiBase):    

    def __init__(self, name, endpoints):
        super().__init__(name=name)
        for klass in [RestApi,
                      Deployment,
                      Stage,
                      GatewayResponse4XX,
                      GatewayResponse5XX,
                      DomainName,
                      BasePathMapping,
                      RecordSet]:
            self.append(klass(name=name))
        for endpoint in endpoints:
            if endpoint["method"].upper()=="GET":
                self += self.init_GET_endpoint(endpoint)
            elif endpoint["method"].upper()=="POST":
                pass
            else:
                raise RuntimeError("endpoint method %s not recognised" % endpoint["method"])

if __name__=="__main__":
    api=PublicApi(name="hello-api",
                  endpoints=[{"name": "hello-get",
                              "method": "GET",
                              "path": "hello",
                              "parameters": ["message"]}])
                             
    import json
    print (json.dumps(api.render(),
                      indent=2))
    
