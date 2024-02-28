# Subclass for Function Role
class FunctionRole(FunctionBase):
    def __init__(self, logs, permissions=None):
        super().__init__(logs["name"], permissions or ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"])
