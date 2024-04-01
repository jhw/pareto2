from pareto2.services import hungarorise as H

from pareto2.services.iam import *
from pareto2.services.sqs import *

from pareto2.recipes.mixins.slackops import SlackAlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

class QueueFunction(L.InlineFunction):
    
    def __init__(self, namespace, queue_namespace):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"queue-url": {"Ref": H(f"{queue_namespace}-queue")}})

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

class TaskQueue(SlackAlertsMixin):    

    def __init__(self,
                 namespace,
                 alerts_namespace = "slack",
                 log_levels = ["error"]):
        super().__init__()
        streaming_namespace = f"{namespace}-task-queue"        
        self.append(Queue(namespace = namespace))
        self.init_streaming(namespace = namespace,
                            streaming_namespace = streaming_namespace)
        self.init_subscription_filters(function_namespace = streaming_namespace,
                                       alerts_namespace = alerts_namespace,
                                       log_levels = log_levels)
        self.init_slackops(namespace = alerts_namespace)

    def init_streaming(self, namespace, streaming_namespace):
        self.append(QueueFunction(namespace = streaming_namespace,
                                  queue_namespace = namespace))
        self.append(Role(namespace = streaming_namespace))
        self.append(QueuePolicy(namespace = streaming_namespace,
                                queue_namespace = namespace))
        self.append(L.SQSEventSourceMapping(namespace = streaming_namespace,
                                            source_arn = {"Fn::GetAtt": [H(f"{namespace}-queue"), "Arn"]}))
            
if __name__ == "__main__":
    pass

    
