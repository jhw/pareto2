from pareto2.ingredients import hungarorise as H
from pareto2.ingredients.iam import Role

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class SingleTableStreamingFunction(lambda_module.InlineFunction):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read())

class SingleTableStreamingRole(Role):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         permissions = ["logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"])

class SingleTableStreamingEventSourceMapping(lambda_module.EventSourceMapping):

    def __init__(self, namespace, function_namespace):
        super.__init__(namespace = namespace,
                       function_namespace = function_namespace)
