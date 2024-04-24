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
        super().__init__(namespace)
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
                               for layername in self.layers]
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
                         code = {"S3Bucket": {"Ref": H("artifacts-bucket")},
                                 "S3Key": {"Ref": H("artifacts-key")}},
                         handler = handler,
                         **kwargs)

class EventInvokeConfig(Resource):

    def __init__(self, namespace, retries = 0):
        super().__init__(namespace)
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
        super().__init__(namespace)
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
        super().__init__(namespace)
        self.source_arn = source_arn
                
    @property
    def aws_properties(self):
        return {
            "EventSourceArn": self.source_arn,
            "FunctionName": {"Ref": H(f"{self.namespace}-function")}
        }

"""
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-maximumretryattempts

- MaximumBatchingWindowInSeconds
  - The maximum amount of time, in seconds, that Lambda spends gathering records before invoking the function.
  - Default (Kinesis, DynamoDB, Amazon SQS event sources): 0
  - define batch_window parameter so you can override if you want, even though default seems sensible
- MaximumRetryAttempts
  - (Kinesis and DynamoDB Streams only) Discard records after the specified number of retries. The default value is -1, which sets the maximum number of retries to infinite. When MaximumRetryAttempts is infinite, Lambda retries failed records until the record expires in the event source.
- StartingPosition
  - The position in a stream from which to start reading. Required for Amazon Kinesis and Amazon DynamoDB.
    - LATEST - Read only new records.
    - TRIM_HORIZON - Process all available records.
    - AT_TIMESTAMP - Specify a time from which to start reading records.
"""

class DynamoDBEventSourceMapping(EventSourceMapping):

    def __init__(self,
                 namespace,
                 source_arn,
                 batch_window = 1, # NB
                 starting_position = "LATEST",
                 retries = 0):
        super().__init__(namespace = namespace,
                         source_arn = source_arn)
        self.batch_window = batch_window
        self.starting_position = starting_position
        self.retries = retries

    @property
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "MaximumBatchingWindowInSeconds": self.batch_window,
            "StartingPosition": self.starting_position,
            "MaximumRetryAttempts": self.retries
        })
        return props

"""
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-batchsize

- BatchSize
  - The maximum number of records in each batch that Lambda pulls from your stream or queue and sends to your function. Lambda passes all of the records in the batch to the function in a single call, up to the payload limit for synchronous invocation (6 MB).
  - Amazon Simple Queue Service – Default 10. For standard queues the max is 10,000. For FIFO queues the max is 10.
  - BatchSize was formerly set at 1 but given inline_code.py iterates over Records and pushes one at a time into EventBridge this doesn't seem to matter any more
"""

class SQSEventSourceMapping(EventSourceMapping):

    def __init__(self,
                 namespace,
                 source_arn,
                 batch_size = 10):
        super().__init__(namespace = namespace,
                         source_arn = source_arn)
        self.batch_size = batch_size
        
    @property
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "BatchSize": self.batch_size
        })
        return props
