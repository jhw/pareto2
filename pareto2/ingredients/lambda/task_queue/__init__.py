from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.iam import Role

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class TaskQueueFunction(lambda_module.InlineFunction):
    
    def __init__(self, namespace, queue_namespace):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"queue-url": {"Ref": H(f"{queue_namespace}-queue")}})

class TaskQueueRole(Role):
    
    def __init__(self, namespace, queue_namespace):
        super().__init__(namespace = namespace,
                         permissions = [{"action": ["sqs:DeleteMessage",
                                                    "sqs:GetQueueAttributes",
                                                    "sqs:ReceiveMessage"],
                                         "resource": {"Fn::GetAtt": [H(f"{queue_namespace}-queue"), "Arn"]}},
                                        {"action": "events:PutEvents"},
                                        {"action": ["logs:CreateLogGroup",
                                                    "logs:CreateLogStream",
                                                    "logs:PutLogEvents"]}])

class TaskQueueEventSourceMapping(lambda_module.EventSourceMapping):

    def __init__(self, namespace, queue_namespace):
        super().__init__(namespace = namespace,
                         source_arn = {"Fn::GetAtt": [H(f"{queue_namespace}-queue"), "Arn"]})
