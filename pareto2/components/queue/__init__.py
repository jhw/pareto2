from pareto.aws.iam import Role as RoleBase

from pareto.aws.lambda import EventSourceMapping
from pareto.aws.lambda import Function as FunctionBase

class Binding(EventSourceMapping):
    
    def __init__(self, queue):
        batch_size = 1 if "batch" not in queue else queue["batch"]
        super().__init__(
            name=f"{queue['name']}-queue-binding",
            function_ref=f"{queue['action']}-function",
            source_arn={"Fn::GetAtt": [f"{queue['name']}-queue", "Arn"]},
            batch_size=batch_size
        )

class DLQFunction(FunctionBase):

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

class DLQFunctionRole(RoleBase):

    def __init__(self, queue, permissions=None):
        super().__init__(queue["name"],
                         permissions or ["logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents",
                                         "sqs:DeleteMessage",
                                         "sqs:GetQueueAttributes",
                                         "sqs:ReceiveMessage"])

class DLQBinding(EventSourceMapping):
    
    def __init__(self, queue, batch_size=1):
        super().__init__(
            name=f"{queue['name']}-queue-dlq-binding",
            function_ref=f"{queue['name']}-queue-dlq-function",
            source_arn={"Fn::GetAtt": [f"{queue['name']}-queue-dlq", "Arn"]},
            batch_size=batch_size
        )
