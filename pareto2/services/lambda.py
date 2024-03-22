from pareto2.services import hungarorise as H
from pareto2.services import uppercase as U
from pareto2.services import Resource

class Function(Resource):

    def __init__(self,
                 namespace,
                 code,
                 handler,
                 layers = [],
                 memory = 512,
                 runtime = "python3.10",
                 timeout = 5,
                 variables = {}):
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
        if self.variables != {}:
            props["Environment"] = {"Variables": {U(k): v
                                                  for k, v in self.variables.items()}}
        if self.layers != []:
            props["Layers"] = [{"Ref": H(f"{layername}-layer-arn")}
                               for layername in self["layers"]]
        return props

class InlineFunction(Function):

    def __init__(self, namespace, code, **kwargs):
        super().__init__(namespace = namespace,
                         code = {"ZipFile": code},
                         handler = "index.handler",
                         **kwargs)

class S3Function(Function):

    def __init__(self, namespace, handler, **kwargs):
        super().__init__(namespace = namespace,
                         code = {"S3Bucket": H("artifacts-bucket"),
                                 "S3Key": H("artifacts-key")},
                         handler = handler,
                         **kwargs)

class EventInvokeConfig(Resource):

    def __init__(self, namespace, retries = 0):
        self.namespace = namespace
        self.retries = retries
    
    @property
    def aws_properties(self):
        return {
            "FunctionName": {"Ref": H(f"{self.namespace}-function")},
            "Qualifier": "$LATEST",
            "MaximumRetryAttempts": self.retries
        }
        
class Permission(Resource):

    def __init__(self, namespace, principal, source_arn = None):
        self.namespace = namespace
        self.principal = principal
        self.source_arn = source_arn
    
    @property
    def aws_properties(self):
        props = {
            "Action": "lambda:InvokeFunction",
            "FunctionName": {"Ref": H(f"{self.namespace}-function")},
            "Principal": self.principal,
        }
        if self.source_arn:
            props["SourceArn"] = self.source_arn
        return props
    
class EventSourceMapping(Resource):

    def __init__(self,
                 namespace,
                 source_arn):
        self.namespace = namespace
        self.source_arn = source_arn
                
    @property
    def aws_properties(self):
        return {
            "EventSourceArn": self.source_arn,
            "FunctionName": {"Ref": H(f"{self.namespace}-function")}
        }



