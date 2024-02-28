from pareto.aws.iam import Role as RoleBase

class DLQFunctionRole(RoleBase):

    def __init__(self, queue, permissions=None):
        super().__init__(queue["name"],
                         permissions or ["logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents",
                                         "sqs:DeleteMessage",
                                         "sqs:GetQueueAttributes",
                                         "sqs:ReceiveMessage"])

