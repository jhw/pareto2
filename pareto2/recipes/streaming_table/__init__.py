from pareto2.services import hungarorise as H
from pareto2.services.dynamodb import StreamingTable as StreamingTableResource
from pareto2.services.iam import *
from pareto2.recipes import *
from pareto2.recipes.mixins.slackops import SlackMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

"""
- makes sense to push errors to Slack in case inline function fails
- doesn't make sense to push warnings as inline code doesn't generate any
- doesn't make sent to have an alarm (at least at the function) as the lambda is "intermediate" and if it is firing excessively, it is likely to be triggering a leaf lambda at the same rate (where an alarm should be implemented)
"""

class StreamingFunction(L.InlineFunction):
    
    def __init__(self, namespace, table_namespace):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
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
        
class StreamingTable(SlackMixin):    
    
    def __init__(self,
                 namespace,
                 log_levels = ["error"]):
        super().__init__()
        streaming_namespace = f"{namespace}-streaming-table"        
        self.append(StreamingTableResource(namespace = namespace))
        self.init_streaming(namespace = namespace,
                            streaming_namespace = streaming_namespace)
        self.init_slack_hooks(function_namespace = streaming_namespace,
                              log_levels = log_levels)
        self.init_slack_resources()

    def init_streaming(self, namespace, streaming_namespace):
        self += [StreamingFunction(namespace = streaming_namespace,
                                   table_namespace = namespace),
                 Role(namespace = streaming_namespace),
                 StreamingPolicy(namespace = streaming_namespace,
                                 table_namespace = namespace),
                 L.DynamoDBEventSourceMapping(namespace = streaming_namespace,
                                              source_arn = {"Fn::GetAtt": [H(f"{namespace}-table"), "StreamArn"]})]
            
if __name__ == "__main__":
    pass

    
