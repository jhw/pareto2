from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Permission(Resource):

    def __init__(self, namespace, function_namespace, source_arn, principal):
        self.namespace = namespace
        self.function_namespace = function_namespace
        self.source_arn = source_arn
        self.principal = principal
    
    @property
    def aws_properties(self):
        return {
            "Action": "lambda:InvokeFunction",
            "FunctionName": {"Ref": H(f"{self.function_namespace}-function")},
            "Principal": self.principal,
            "SourceArn": self.source_arn
        }

