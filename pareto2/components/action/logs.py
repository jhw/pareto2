from pareto.aws.iam import Role as RoleBase

class LogsRole(RoleBase):

    def __init__(self, logs, permissions=None):
        super().__init__(logs["name"],
                         permissions or ["logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents"])
