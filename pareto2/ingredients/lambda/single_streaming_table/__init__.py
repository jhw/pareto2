from pareto2.ingredients import hungarorise as H
from pareto2.ingredients.iam import Role

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class SingleStreamingTableFunction(lambda_module.InlineFunction):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read())

class SingleStreamingTableRole(Role):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         permissions = ["dynamodb:GetRecords",
                                        "dynamodb:GetShardIterator",
                                        "dynamodb:DescribeStream",
                                        "dynamodb:ListStreams",
                                        "events:PutEvents",
                                        "logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"])

class SingleStreamingTableEventSourceMapping(lambda_module.EventSourceMapping):

    def __init__(self, namespace, table_namespace):
        super().__init__(namespace = namespace,
                         source_arn = {"Fn::GetAtt": [H(f"{table_namespace}-table"), "StreamArn"]})
