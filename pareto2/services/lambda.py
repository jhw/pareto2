from pareto2.services import hungarorise as H
from pareto2.services import uppercase as U
from pareto2.services import Resource

class Function(Resource):

    def __init__(self,
                 namespace,
                 code,
                 handler = "index.handler",
                 memory = 512,
                 runtime = "python3.10",
                 timeout = 5):
        self.namespace = namespace
        self.code = code
        self.handler = handler
        self.memory = memory
        self.runtime = runtime
        self.timeout = timeout

    @property
    def aws_properties(self):
        props = {
            "Code": {"ZipFile": self.code},
            "Handler": self.handler,
            "MemorySize": self.memory,
            "Role": {"Fn::GetAtt": [H(f"{self.namespace}-role"), "Arn"]},
            "Runtime": self.runtime,
            "Timeout": self.timeout
        }
        if self.variables != []:            
            props["Environment"] = {"Variables": {U(k): {"Ref": H(k)}
                                                  for k in self.variables}}
        return props
            
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


