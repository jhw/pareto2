# Subclass for DLQ Function Role
class DLQFunctionRole(FunctionBase):
    def __init__(self, queue, permissions=None):
        super().__init__(queue["name"], permissions or ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ReceiveMessage"])

