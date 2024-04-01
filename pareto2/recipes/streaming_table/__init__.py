from pareto2.services import hungarorise as H

from pareto2.services.dynamodb import StreamingTable as StreamingTableResource
from pareto2.services.iam import *

from pareto2.recipes.mixins.slackops import SlackAlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

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
        self.append(L.DynamoDBEventSourceMapping(namespace = streaming_namespace,
                                                 source_arn = {"Fn::GetAtt": [H(f"{namespace}-table"), "StreamArn"]}))
            
if __name__ == "__main__":
    pass

    
