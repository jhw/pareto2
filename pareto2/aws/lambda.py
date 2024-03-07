from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Function(Resource):

    def __init__(self,
                 component_name,
                 code,
                 runtime_version='3.10',
                 handler='index.handler',
                 size='default',
                 timeout='default',
                 envvars={},
                 layers=[]):
        self.component_name = component_name
        self.code = code
        self.runtime_version = runtime_version
        self.handler = handler
        self.size = size
        self.timeout = timeout
        self.envvars = envvars
        self.layers = layers

    @property
    def aws_properties(self):
        environment_variables = {k: {"Ref": v} for k, v in self.envvars.items()}        
        props = {
            "Role": {"Fn::GetAtt": [H(f"{self.component_name}-function-role"), "Arn"]},
            "MemorySize": {"Ref": H(f"memory-size-{self.size}")},
            "Timeout": {"Ref": H(f"timeout-{self.timeout}")},
            "Code": self.code,
            "Handler": self.handler,
            "Runtime": {"Fn::Sub": f"python{self.runtime_version}"},
            "Environment": {"Variables": environment_variables} if environment_variables else None
        }        
        if self.layers:
            props["Layers"] = [{"Ref": layer} for layer in self.layers]        
        return props

class Permission(Resource):

    def __init__(self, component_name, source_arn=None, principal=None):
        self.component_name = component_name
        self.source_arn = source_arn
        self.principal = principal
    
    @property
    def aws_properties(self):
        props = {
            "Action": "lambda:InvokeFunction",
            "FunctionName": {"Ref": H(f"{self.component_name}-function")},
            "Principal": self.principal
        }
        if self.source_arn:
            props["SourceArn"] = self.source_arn
        return props

class EventSourceMapping(Resource):
    
    def __init__(self,
                 component_name,
                 source_arn,
                 batch_size=1,
                 starting_position=None,
                 maximum_batching_window_in_seconds=None,
                 maximum_retry_attempts=None):
        self.component_name = component_name
        self.source_arn = source_arn
        self.batch_size = batch_size
        self.starting_position = starting_position
        self.maximum_batching_window_in_seconds = maximum_batching_window_in_seconds
        self.maximum_retry_attempts = maximum_retry_attempts

    @property
    def aws_properties(self):
        props = {
            "FunctionName": {"Ref": H(f"{self.component_name}-function")},
            "EventSourceArn": self.source_arn,
            "BatchSize": self.batch_size
        }
        if self.starting_position:
            props["StartingPosition"] = self.starting_position
        if self.maximum_batching_window_in_seconds is not None:
            props["MaximumBatchingWindowInSeconds"] = self.maximum_batching_window_in_seconds
        if self.maximum_retry_attempts is not None:
            props["MaximumRetryAttempts"] = self.maximum_retry_attempts
        return props

class EventInvokeConfig(Resource):
    
    def __init__(self, component_name, retries=0):
        self.component_name = component_name
        self.retries = retries

    @property
    def aws_properties(self):
        return {
            "MaximumRetryAttempts": self.retries,
            "FunctionName": {"Ref": H(f"{self.component_name}-function")},
            "Qualifier": "$LATEST"
        }
