from pareto2.services import hungarorise as H
from pareto2.services.dynamodb import StreamTable as StreamTableResource
from pareto2.services.iam import *
from pareto2.recipes import *
from pareto2.recipes.mixins.alerts import AlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

"""
- makes sense to push errors to Slack in case inline function fails
- doesn't make sense to push warnings as inline code doesn't generate any
- doesn't make sent to have an alarm (at least at the function) as the lambda is "intermediate" and if it is firing excessively, it is likely to be triggering a leaf lambda at the same rate (where an alarm should be implemented)
"""

class StreamFunction(L.InlineFunction):
    
    def __init__(self, namespace, table_namespace):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"app-table": {"Ref": H(f"{table_namespace}-table")}})

class StreamPolicy(Policy):
    
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
        
class StreamTable(AlertsMixin):    
    
    def __init__(self,
                 namespace,
                 batch_window = 1,
                 indexes = [],
                 log_levels = ["error"]):
        super().__init__()
        stream_namespace = f"{namespace}-stream-table"        
        self.append(StreamTableResource(namespace = namespace,
                                        indexes = indexes))
        self.init_stream(namespace = namespace,
                            stream_namespace = stream_namespace,
                            batch_window = batch_window)
        self.init_alert_hooks(function_namespace = stream_namespace,
                              log_levels = log_levels)
        self.init_alert_resources()

    def init_stream(self, namespace, stream_namespace, batch_window):
        self += [StreamFunction(namespace = stream_namespace,
                                table_namespace = namespace),
                 Role(namespace = stream_namespace),
                 StreamPolicy(namespace = stream_namespace,
                              table_namespace = namespace),
                 L.DynamoDBEventSourceMapping(namespace = stream_namespace,
                                              batch_window = batch_window,
                                              source_arn = {"Fn::GetAtt": [H(f"{namespace}-table"), "StreamArn"]})]
            
if __name__ == "__main__":
    pass

    
