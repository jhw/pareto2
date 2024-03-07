from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Function(Resource):

    def __init__(self, component_name, code, runtime_version='runtime-version', handler='index.handler', size='default-size', timeout='default-timeout', envvars=None, layers=None):
        self.component_name = component_name
        self.code = code
        self.runtime_version = runtime_version
        self.handler = handler
        self.size = size
        self.timeout = timeout
        self.envvars = envvars or {}
        self.layers = layers or []

    @property
    def resource_name(self):
        return H(f"{self.component_name}-function")

    @property
    def aws_resource_type(self):
        return "AWS::Lambda::Function"

    @property
    def aws_properties(self):
        role_name = H(f"{self.component_name}-function-role")
        memory_size = H(f"memory-size-{self.size}")
        timeout = H(f"timeout-{self.timeout}")
        runtime = H(f"python${{{self.runtime_version}}}")
        environment_variables = {k: {"Ref": v} for k, v in self.envvars.items()}
        
        props = {
            "Role": {"Fn::GetAtt": [role_name, "Arn"]},
            "MemorySize": {"Ref": memory_size},
            "Timeout": {"Ref": timeout},
            "Code": self.code,
            "Handler": self.handler,
            "Runtime": {"Fn::Sub": runtime},
            "Environment": {"Variables": environment_variables} if environment_variables else None
        }
        
        if self.layers:
            props["Layers"] = [{"Ref": layer} for layer in self.layers]
        
        return props

class Permission(Resource):

    def __init__(self, component_name, action=None, source_arn=None, principal=None):
        self.component_name = component_name
        self.action = action
        self.source_arn = source_arn
        self.principal = principal
    
    @property
    def resource_name(self):
        return H(f"{self.component_name}-permission")
    
    @property
    def aws_resource_type(self):
        return "AWS::Lambda::Permission"
    
    @property
    def aws_properties(self):
        props = {
            "Action": "lambda:InvokeFunction",
            "FunctionName": {"Ref": H(f"{self.action}-function")},
            "Principal": self.principal
        }
        if self.source_arn:
            props["SourceArn"] = self.source_arn
        return props

class EventSourceMapping(Resource):
    
    def __init__(self, component_name, function, source_arn, batch_size=1, starting_position=None, maximum_batching_window_in_seconds=None, maximum_retry_attempts=None):
        self.component_name = component_name
        self.function = function
        self.source_arn = source_arn
        self.batch_size = batch_size
        self.starting_position = starting_position
        self.maximum_batching_window_in_seconds = maximum_batching_window_in_seconds
        self.maximum_retry_attempts = maximum_retry_attempts

    @property
    def resource_name(self):
        return H(f"{self.component_name}-event-source-mapping")

    @property
    def aws_resource_type(self):
        return "AWS::Lambda::EventSourceMapping"

    @property
    def aws_properties(self):
        props = {
            "FunctionName": {"Ref": self.function},
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
    
    def __init__(self, component_name, function_name, retries=0):
        self.component_name = component_name
        self.function_name = function_name
        self.retries = retries

    @property
    def resource_name(self):
        return H(f"{self.component_name}-function-event-config")

    @property
    def aws_resource_type(self):
        return "AWS::Lambda::EventInvokeConfig"

    @property
    def aws_properties(self):
        return {
            "MaximumRetryAttempts": self.retries,
            "FunctionName": {"Ref": self.function_name},
            "Qualifier": "$LATEST"
        }
