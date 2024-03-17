from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.iam import *
from pareto2.ingredients.logs import *

from pareto2.recipes import Recipe

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")
slack_module = importlib.import_module("pareto2.ingredients.lambda.slack")

"""
- LogNamespace is a singleton namespace 
"""

LogNamespace, LogLevels = "logs", ["warning", "error"]

class EventWorker(Recipe):    

    def __init__(self,
                 namespace,
                 worker,
                 logging_namespace = LogNamespace,
                 log_levels = LogLevels):
        super().__init__()
        self.init_worker(namespace = namespace,
                         worker = worker)
        self.init_log_subscriptions(parent_ns = namespace,
                                    worker = worker,
                                    log_levels = log_levels)
        self.init_logs(parent_ns = logging_namespace,
                       log_levels = log_levels)

    def init_worker(self, namespace, worker):
        self.append(self.init_function(namespace = namespace,
                                       worker = worker))
        self.append(lambda_module.EventInvokeConfig(namespace = namespace))
        self.append(self.init_role(namespace = namespace,
                                   worker = worker))
        self.append(LogGroup(namespace = namespace))
        self.append(LogStream(namespace = namespace))
        
    def function_kwargs(self, worker):
        kwargs = {}
        for attr in ["code",
                     "handler",
                     "memory",
                     "timeout",
                     "runtime",
                     "layers"]:
            if attr in worker:
                kwargs[attr] = worker[attr]
        return kwargs

    def init_function(self, namespace, worker):
        fn = lambda_module.InlineFunction if "code" in worker else lambda_module.S3Function
        return (fn(namespace = namespace,
                   **self.function_kwargs(worker)))

    def wildcard_override(fn):
        def wrapped(self, *args, **kwargs):
            permissions=fn(self, *args, **kwargs)
            wildcards=set([permission.split(":")[0]
                           for permission in permissions
                           if permission.endswith(":*")])
            return [permission for permission in permissions
                    if (permission.endswith(":*") or
                        permission.split(":")[0] not in wildcards)]
        return wrapped
    
    @wildcard_override
    def role_permissions(self, worker,
                         defaults = ["logs:CreateLogGroup",
                                     "logs:CreateLogStream",
                                     "logs:PutLogEvents"]):
        permissions = set(defaults)
        if "permissions" in worker:
            permissions.update(set(worker["permissions"]))
        return sorted(list(permissions))

    def init_role(self, namespace, worker):
        return Role(namespace = namespace,
                    permissions = self.role_permissions(worker))

    def init_log_subscriptions(self, parent_ns, worker, log_levels):
        for log_level in log_levels:        
            child_ns = f"{parent_ns}-{log_level}"
            subscriptionfn = eval(H(f"{log_level}-subscription-filter"))
            self.append(subscriptionfn(namespace = parent_ns,
                                       logging_namespace = child_ns))
    
    def init_logs(self, parent_ns, log_levels):
        for log_level in log_levels:
            child_ns = f"{parent_ns}-{log_level}"
            self.append(slack_module.SlackWebhookFunction(namespace = child_ns,
                                                          log_level = log_level))
            self.append(slack_module.SlackWebhookRole(namespace = child_ns))
            self.append(slack_module.SlackWebhookPermission(namespace = child_ns))
            
if __name__ == "__main__":
    pass

    
