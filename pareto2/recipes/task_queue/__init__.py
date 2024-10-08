from pareto2.recipes import *
from pareto2.recipes.mixins.alerts import AlertsMixin
from pareto2.services import hungarorise as H
from pareto2.services.iam import *
from pareto2.services.sqs import *

import importlib
L = importlib.import_module("pareto2.services.lambda")

"""
- makes sense to push errors to Slack in case inline function fails
- doesn't make sense to push warnings as inline code doesn't generate any
"""

class QueueFunction(L.InlineFunction):
    
    def __init__(self, namespace, queue_namespace):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"app-queue": {"Ref": H(f"{queue_namespace}-queue")}})

class QueuePolicy(Policy):
    
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

class TaskQueue(AlertsMixin):    
    
    def __init__(self,
                 namespace,
                 batch_size = 10,
                 log_levels = ["error"]):
        super().__init__()
        queue_namespace = f"{namespace}-task-queue"        
        self.append(Queue(namespace = namespace))
        self.init_queue(namespace = namespace,
                        queue_namespace = queue_namespace,
                        batch_size = batch_size)
        self.init_alert_hooks(namespace = queue_namespace,
                              log_levels = log_levels)
        self.init_alert_resources()

    def init_queue(self, namespace, queue_namespace, batch_size):
        self += [QueueFunction(namespace = queue_namespace,
                               queue_namespace = namespace),
                 Role(namespace = queue_namespace),
                 QueuePolicy(namespace = queue_namespace,
                             queue_namespace = namespace),
                 L.SQSEventSourceMapping(namespace = queue_namespace,
                                         batch_size = batch_size,
                                         source_id = H(f"{namespace}-queue"),
                                         source_arn = {"Fn::GetAtt": [H(f"{namespace}-queue"), "Arn"]})]
            
if __name__ == "__main__":
    pass

    
