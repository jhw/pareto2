from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Function(Resource):

    def __init__(self, namespace,
                 handler = "index.handler",
                 memory = 512,
                 runtime = "python3.10",
                 timeout = 5):
        self.namespace = namespace
        self.handler = handler
        self.memory = memory
        self.runtime = runtime
        self.timeout = timeout

    @property
    def aws_properties(self):
        return {
            "Handler": self.handler,
            "MemorySize": self.memory,
            "Runtime": self.runtime,
            "Timeout": self.timeout
        }
    
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


