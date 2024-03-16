from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import uppercase as U
from pareto2.ingredients import Resource

class Function(Resource):

    def __init__(self,
                 namespace,
                 code,
                 handler,
                 layers = [],
                 memory = 512,
                 runtime = "python3.10",
                 timeout = 5,
                 variables = []):
        self.namespace = namespace
        self.code = code
        self.handler = handler
        self.layers = layers
        self.memory = memory
        self.runtime = runtime
        self.timeout = timeout
        self.variables = variables

    @property
    def aws_properties(self):
        props = {
            "Code": self.code,
            "Handler": self.handler,
            "MemorySize": self.memory,
            "Role": {"Fn::GetAtt": [H(f"{self.namespace}-role"), "Arn"]},
            "Runtime": self.runtime,
            "Timeout": self.timeout
        }
        if self.variables != []:            
            props["Environment"] = {"Variables": {U(k): {"Ref": H(k)}
                                                  for k in self.variables}}
        if self.layers != []:
            props["Layers"] = [{"Ref": H(f"{layername}-layer-arn")}
                               for layername in self["layers"]]
        return props

class InlineFunction(Function):

    def __init__(self, namespace, code, **kwargs):
        super().__init__(namespace,
                         code = {"ZipFile": code},
                         handler = "index.handler",
                         **kwargs)

class S3Function(Function):

    def __init__(self, namespace, handler, **kwargs):
        super().__init__(namespace,
                         code = {"S3Bucket": H("artifacts-bucket"),
                                 "S3Key": H("artifacts-key")},
                         handler = handler,
                         **kwargs)
    
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


