# from pareto2.aws.lambda import Permission as PermissionsBase

import importlib
lambda_module = importlib.import_module("pareto2.aws.lambda")
PermissionBase = lambda_module.Permission

class Permission(PermissionBase):
    
    def __init__(self, name, function_name, method, path):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{name}/{method}/{path}"}
        super().__init__(name=name,
                         function_name=function_name,
                         source_arn=source_arn,
                         principal="apigateway.amazonaws.com")



