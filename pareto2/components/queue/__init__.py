from pareto.aws.iam import Role as RoleBase

from pareto.aws.lambda import EventSourceMapping as EventSourceMappingBase
from pareto.aws.lambda import Function as FunctionBase

from pareto.aws.sqs import Queue as QueueBase

class Queue(QueueBase):

    def __init__(self, queue_name, max_receive_count=1):
        super().__init__(queue_name)
        self.max_receive_count = max_receive_count

    @property
    def aws_properties(self):
        dlq_arn = {"Fn::GetAtt": [f"{self.queue_name}-queue-dlq", "Arn"]}
        redrive_policy = {
            "deadLetterTargetArn": dlq_arn,
            "maxReceiveCount": self.max_receive_count

class EventSourceMapping(EventSourceMappingBase):
    
    def __init__(self, queue):
        batch_size = 1 if "batch" not in queue else queue["batch"]
        super().__init__(
            name=f"{queue['name']}-queue-binding",
            function_ref=f"{queue['action']}-function",
            source_arn={"Fn::GetAtt": [f"{queue['name']}-queue", "Arn"]},
            batch_size=batch_size
        )

class DeadLetterQueue(QueueBase):
            
    def __init__(self, queue_name):
        super().__init__(queue_name)

    @property
    def resource_name(self):
        return f"{self.queue_name}-queue-dlq"
            
class DeadLetterQueueFunction(FunctionBase):

    def __init__(self, queue,
                 size='default',
                 timeout='default',
                 envvars=None,
                 code=SlackFunctionCode):
        super().__init__(queue["name"],
                         "queue-dlq-function-role",
                         {"ZipFile": code},
                         size=size,
                         timeout=timeout,
                         envvars={env: {"Ref": env} for env in envvars})

class DeadLetterQueueFunctionRole(RoleBase):

    def __init__(self, queue, permissions=None):
        super().__init__(queue["name"],
                         permissions or ["logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents",
                                         "sqs:DeleteMessage",
                                         "sqs:GetQueueAttributes",
                                         "sqs:ReceiveMessage"])

class DeadLetterQueueBinding(EventSourceMapping):
    
    def __init__(self, queue, batch_size=1):
        super().__init__(
            name=f"{queue['name']}-queue-dlq-binding",
            function_ref=f"{queue['name']}-queue-dlq-function",
            source_arn={"Fn::GetAtt": [f"{queue['name']}-queue-dlq", "Arn"]},
            batch_size=batch_size
        )
