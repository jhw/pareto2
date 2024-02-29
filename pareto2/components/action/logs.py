from pareto.aws.iam import Role as RoleBase
from pareto.aws.lambda import Function as FunctionBase

class LogsFunction(FunctionBase):

    def __init__(self, logs, code=SlackFunctionCode):
        envvars = {
            "slack-webhook-url": "slack-webhook-url",
            "slack-logging-level": logs["level"]
        }
        super().__init__(logs["name"],
                         "logs-function-role",
                         {"ZipFile": code},
                         size=logs["function"]["size"],
                         timeout=logs["function"]["timeout"],
                         envvars=envvars)

class LogsRole(RoleBase):

    def __init__(self, logs, permissions=None):
        super().__init__(logs["name"],
                         permissions or ["logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents"])
