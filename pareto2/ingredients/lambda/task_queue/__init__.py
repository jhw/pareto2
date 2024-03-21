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

"""
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-batchsize
---
- BatchSize
  - The maximum number of records in each batch that Lambda pulls from your stream or queue and sends to your function. Lambda passes all of the records in the batch to the function in a single call, up to the payload limit for synchronous invocation (6 MB).
  - Amazon Simple Queue Service – Default 10. For standard queues the max is 10,000. For FIFO queues the max is 10.
  - BatchSize was formerly set at 1 but given inline_code.py iterates over Records and pushes one at a time into EventBridge this doesn't seem to matter any more
"""
        
class TaskQueueEventSourceMapping(lambda_module.EventSourceMapping):

    def __init__(self, namespace, queue_namespace):
        super().__init__(namespace = namespace,
                         source_arn = {"Fn::GetAtt": [H(f"{queue_namespace}-queue"), "Arn"]})
