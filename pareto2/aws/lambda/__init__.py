class Function:

    def __init__(self, name, role_suffix, code, runtime_version='runtime-version', handler='index.handler', size='default-size', timeout='default-timeout', envvars=None, layers=None):
        self.name = name
        self.role_suffix = role_suffix
        self.code = code
        self.runtime_version = runtime_version
        self.handler = handler
        self.size = size
        self.timeout = timeout
        self.envvars = envvars or {}
        self.layers = layers or []

    @property
    def resource_name(self):
        return f"{self.name}-function"

    @property
    def aws_resource_type(self):
        return "AWS::Lambda::Function"

    @property
    def aws_properties(self):
        role_name = f"{self.name}-{self.role_suffix}"
        memory_size = f"memory-size-{self.size}"
        timeout = f"timeout-{self.timeout}"
        runtime = f"python${{{self.runtime_version}}}"
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

class Permission:

    def __init__(self, name, action=None, source_arn=None, principal=None):
        self.name = name
        self.action = action
        self.source_arn = source_arn
        self.principal = principal
    
    @property
    def resource_name(self):
        return f"{self.name}-permission"
    
    @property
    def aws_resource_type(self):
        return "AWS::Lambda::Permission"
    
    @property
    def aws_properties(self):
        props = {
            "Action": "lambda:InvokeFunction",
            "FunctionName": {"Ref": f"{self.action}-function"},
            "Principal": self.principal
        }
        if self.source_arn:
            props["SourceArn"] = self.source_arn
        return props

class EventSourceMapping:
    
    def __init__(self, name, function_ref, source_arn, batch_size=1, starting_position=None, maximum_batching_window_in_seconds=None, maximum_retry_attempts=None):
        self.name = name
        self.function_ref = function_ref
        self.source_arn = source_arn
        self.batch_size = batch_size
        self.starting_position = starting_position
        self.maximum_batching_window_in_seconds = maximum_batching_window_in_seconds
        self.maximum_retry_attempts = maximum_retry_attempts

    @property
    def resource_name(self):
        return f"{self.name}-event-source-mapping"

    @property
    def aws_resource_type(self):
        return "AWS::Lambda::EventSourceMapping"

    @property
    def aws_properties(self):
        props = {
            "FunctionName": {"Ref": self.function_ref},
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
