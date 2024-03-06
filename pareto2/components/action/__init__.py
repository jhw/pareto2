from pareto2.aws.lambda import EventInvokeConfig as EventInvokeConfigBase
from pareto2.aws.lambda import Function as FunctionBase

from pareto2.aws.iam import Role as RoleBase

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

class FunctionRole(RoleBase):
    
    def __init__(self, component, base_permissions=[], additional_permissions=None):
        self.component_name = component["name"]
        self.base_permissions = base_permissions
        self.additional_permissions = additional_permissions or []
        super().__init__(self.component_name, self._compile_permissions())

    def _compile_permissions(self):
        # Combine base permissions with additional ones
        return sorted(list(set(self.base_permissions + self.additional_permissions)))

    @property
    def policy_document(self):
        # Specific implementation for generating policy document
        return policy_document(self.permissions, self.resource)

    @property
    def assume_role_policy_document(self):
        # Assume role policy, potentially customized based on service_principal
        return assume_role_policy_document(self.service_principal)
        
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
