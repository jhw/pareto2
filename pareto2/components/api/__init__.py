# from pareto2.aws.lambda import Permission as PermissionsBase

from pareto2.aws import hungarorise as H

import importlib
lambda_module = importlib.import_module("pareto2.aws.lambda")
PermissionBase = lambda_module.Permission

class Permission(PermissionBase):
    
    def __init__(self, namespace, function_namespace, method, path):
        restapiref, stageref = H(f"{namespace}-rest-api"), H(f"{namespace}-stage")
        source_arn = {"Fn::Sub": "arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${%s}/${%s}/%s/%s" % (restapiref, stageref, method, path)}
        super().__init__(namespace=namespace,
                         function_namespace=function_namespace,
                         source_arn=source_arn,
                         principal="apigateway.amazonaws.com")



