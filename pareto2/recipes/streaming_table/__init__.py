from pareto2.services import hungarorise as H

from pareto2.services.dynamodb import StreamingTable as StreamingTableResource
from pareto2.services.iam import *

from pareto2.recipes.mixins.slackops import SlackAlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

class StreamingFunction(L.InlineFunction):
    
    def __init__(self, namespace, table_namespace):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"table-name": {"Ref": H(f"{table_namespace}-table")}})

class StreamingPolicy(Policy):
    
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

"""
Actually am having some problems with this pattern; sometimes you can put an item to DynamoDB and somehow the streaming function doesn't get triggered; but at other times it works just fine

I am wondering if this is somehow related to the batching window parameter; it feels like whatever is happening or going wrong, it's happening at the EventSourceMapping level; no for now am reverting to the parameters used in pareto2 0.7.x
"""

class StreamingEventSourceMapping(L.EventSourceMapping):

    def __init__(self,
                 namespace,
                 table_namespace,
                 batch_window = 1, # NB
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
        
class StreamingTable(SlackAlertsMixin):    

    def __init__(self,
                 namespace,
                 alerts_namespace = "slack",
                 log_levels = ["error"]):
        super().__init__()
        streaming_namespace = f"{namespace}-streaming-table"        
        self.append(StreamingTableResource(namespace = namespace))
        self.init_streaming(namespace = namespace,
                            streaming_namespace = streaming_namespace)
        self.init_subscription_filters(function_namespace = streaming_namespace,
                                       alerts_namespace = alerts_namespace,
                                       log_levels = log_levels)
        self.init_slackops(namespace = alerts_namespace)

    def init_streaming(self, namespace, streaming_namespace):
        self.append(StreamingFunction(namespace = streaming_namespace,
                                      table_namespace = namespace))
        self.append(Role(namespace = streaming_namespace))
        self.append(StreamingPolicy(namespace = streaming_namespace,
                                    table_namespace = namespace))
        self.append(StreamingEventSourceMapping(namespace = streaming_namespace,
                                                table_namespace = namespace))
            
if __name__ == "__main__":
    pass

    
