from pareto2.aws.apigateway import LambdaProxyMethod
from pareto2.aws.apigateway import Resource as APIGWResource

# from pareto2.aws.lambda import Permission as PermissionsBase

import importlib
lambda_module = importlib.import_module("pareto2.aws.lambda")
PermissionBase = lambda_module.Permission

from pareto2.components import Component

class Permission(PermissionBase):
    
    def __init__(self, name, function_name, method, path):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{name}/{method}/{path}"}
        super().__init__(name=name,
                         function_name=function_name,
                         source_arn=source_arn,
                         principal="apigateway.amazonaws.com")

"""
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

    def init_POST_endpoint(self, endpoint):
        return [APIGWResource(name=self.name,
                              path=endpoint["path"]),
                LambdaProxyMethod(name=self.name,
                                  function_name="whatevs",
                                  method=endpoint["method"],
                                  parameters=endpoint["parameters"])]


