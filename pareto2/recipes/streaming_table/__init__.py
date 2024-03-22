from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.dynamodb import StreamingTable as StreamingTableResource
from pareto2.ingredients.iam import *

from pareto2.recipes import Recipe

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class StreamingTableFunction(lambda_module.InlineFunction):
    
    def __init__(self, namespace, table_namespace):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"table-name": {"Ref": H(f"{table_namespace}-table")}})

class StreamingTableRole(Role):
    
    def __init__(self, namespace, table_namespace):
        super().__init__(namespace = namespace)

        
class StreamingTablePolicy(Policy):
    
    def __init__(self, namespace, table_namespace):
        super().__init__(namespace = namespace,
                         permissions = [{"action": ["dynamodb:GetRecords",
                                                    "dynamodb:GetShardIterator",
                                                    "dynamodb:DescribeStream",
                                                    "dynamodb:ListStreams"],
                                         "resource": {"Fn::GetAtt": [H(f"{table_namespace}-table"), "StreamArn"]}},
                                        {"action": "events:PutEvents"},
                                        {"action": ["logs:CreateLogGroup",
                                                    "logs:CreateLogStream",
                                                    "logs:PutLogEvents"]}])

"""
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-maximumretryattempts
---
- MaximumBatchingWindowInSeconds
  - The maximum amount of time, in seconds, that Lambda spends gathering records before invoking the function.
  - Default (Kinesis, DynamoDB, Amazon SQS event sources): 0
  - define batch_window parameter so you can override if you want, even though default seems sensible
- MaximumRetryAttempts
  - (Kinesis and DynamoDB Streams only) Discard records after the specified number of retries. The default value is -1, which sets the maximum number of retries to infinite. When MaximumRetryAttempts is infinite, Lambda retries failed records until the record expires in the event source.
- StartingPosition
  - The position in a stream from which to start reading. Required for Amazon Kinesis and Amazon DynamoDB.
    - LATEST - Read only new records.
    - TRIM_HORIZON - Process all available records.
    - AT_TIMESTAMP - Specify a time from which to start reading records.
"""
        
class StreamingTableEventSourceMapping(lambda_module.EventSourceMapping):

    def __init__(self,
                 namespace,
                 table_namespace,
                 batch_window = 0,
                 starting_position = "LATEST",
                 retries = 0):
        super().__init__(namespace = namespace,
                         source_arn = {"Fn::GetAtt": [H(f"{table_namespace}-table"), "StreamArn"]})
        self.batch_window = batch_window
        self.starting_position = starting_position
        self.retries = retries

    @property
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "MaximumBatchingWindowInSeconds": self.batch_window,
            "StartingPosition": self.starting_position,
            "MaximumRetryAttempts": self.retries
        })
        return props
        
class StreamingTable(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(StreamingTableResource(namespace = namespace))
        self.init_streaming(parent_ns = namespace)        

    def init_streaming(self, parent_ns):
        child_ns = f"{parent_ns}-streaming-table"        
        for klass in [StreamingTableFunction,
                      StreamingTableRole,
                      StreamingTablePolicy,
                      StreamingTableEventSourceMapping]:
            self.append(klass(namespace = child_ns,
                              table_namespace = parent_ns))
            
if __name__ == "__main__":
    pass

    
