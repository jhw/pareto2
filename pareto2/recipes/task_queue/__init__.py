from pareto2.services import hungarorise as H

from pareto2.services.iam import *
from pareto2.services.sqs import *

from pareto2.recipes import Recipe

import importlib

L = importlib.import_module("pareto2.services.lambda")

class QueueFunction(L.InlineFunction):
    
    def __init__(self, namespace, queue_namespace):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
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

"""
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-batchsize
---
- BatchSize
  - The maximum number of records in each batch that Lambda pulls from your stream or queue and sends to your function. Lambda passes all of the records in the batch to the function in a single call, up to the payload limit for synchronous invocation (6 MB).
  - Amazon Simple Queue Service – Default 10. For standard queues the max is 10,000. For FIFO queues the max is 10.
  - BatchSize was formerly set at 1 but given inline_code.py iterates over Records and pushes one at a time into EventBridge this doesn't seem to matter any more
"""
        
class QueueEventSourceMapping(L.EventSourceMapping):

    def __init__(self, namespace, queue_namespace):
        super().__init__(namespace = namespace,
                         source_arn = {"Fn::GetAtt": [H(f"{queue_namespace}-queue"), "Arn"]})

class TaskQueue(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        child_ns = f"{namespace}-task-queue"        
        self.append(Queue(namespace = namespace))
        self.append(QueueFunction(namespace = child_ns,
                                  queue_namespace = namespace))
        self.append(Role(namespace = child_ns))
        self.append(QueuePolicy(namespace = child_ns,
                                queue_namespace = namespace))
        self.append(QueueEventSourceMapping(namespace = child_ns,
                                            queue_namespace = namespace))


            
if __name__ == "__main__":
    pass

    
