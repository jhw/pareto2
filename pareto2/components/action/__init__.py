from pareto.aws.lambda import EventInvokeConfig as EventInvokeConfigBase
from pareto.aws.lambda import Function as FunctionBase

from pareto.aws.iam import Role as RoleBase

class Function(FunctionBase):
    
    def __init__(self, action):
        code = {
            "S3Bucket": {"Ref": "artifacts-bucket"},
            "S3Key": {"Ref": "artifacts-key"}
        }
        envvars = action["env"]["variables"] if "env" in action else {}
        layers = [f"{pkgname}-layer-arn" for pkgname in action.get("layers", [])]
        handler = f"{action['path'].replace('-', '/')}/index.handler"
        super().__init__(action["name"],
                         "function-role",
                         code,
                         size=action["size"],
                         timeout=action["timeout"],
                         envvars=envvars,
                         layers=layers,
                         handler=handler)

class EventInvokeConfig(EventInvokeConfigBase):

    def __init__(self, action, retries=0):
        super().__init__(action["name"], f"{action['name']}-function", retries)
        
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
