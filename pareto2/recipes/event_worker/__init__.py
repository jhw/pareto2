from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.events import *
from pareto2.ingredients.iam import *
from pareto2.ingredients.logs import *

from pareto2.recipes import Recipe

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

"""
- LogNamespace is a singleton namespace 
"""

LogNamespace, LogLevels = "logs", ["warning", "error"]

"""
- NB slack-webhook-url defined declaratively / as a Ref, so appears as a top level Parameter
- remember one Slack webhook per application
"""

class SlackFunction(lambda_module.InlineFunction):

    def __init__(self, namespace, log_level):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})

class SlackRole(Role):

    def __init__(self, namespace):
        super().__init__(namespace = namespace)
        
class SlackPolicy(Policy):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         permissions = ["logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"])
        
class SlackPermission(lambda_module.Permission):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         principal = "logs.amazonaws.com")

class EventPermission(lambda_module.Permission):

    def __init__(self, namespace, function_namespace):
        source_arn = {"Fn::GetAtt": [H(f"{namespace}-rule"), "Arn"]}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "events.amazonaws.com")

class EventWorker(Recipe):    

    def __init__(self,
                 namespace,
                 worker,
                 logging_namespace = LogNamespace,
                 log_levels = LogLevels):
        super().__init__()
        self.init_worker(namespace = namespace,
                         worker = worker)
        self.init_log_subscriptions(namespace = namespace,
                                    logging_namespace = logging_namespace,
                                    worker = worker,
                                    log_levels = log_levels)
        self.init_logs(parent_ns = logging_namespace,
                       log_levels = log_levels)

    def init_worker(self, namespace, worker):
        self.append(self.init_function(namespace = namespace,
                                       worker = worker))
        self.append(lambda_module.EventInvokeConfig(namespace = namespace))
        self += self.init_role_and_policy(namespace = namespace,
                                          worker = worker)
        for event in worker["events"]:
            self.init_event_rule(parent_ns = namespace,
                                 event = event)
        self.append(LogGroup(namespace = namespace))
        self.append(LogStream(namespace = namespace))
        
    def init_function(self, namespace, worker):
        fn = lambda_module.InlineFunction if "code" in worker else lambda_module.S3Function
        return (fn(namespace = namespace,
                   **self.function_kwargs(worker)))
    
    def init_role_and_policy(self, namespace, worker):
        return  [
            Role(namespace = namespace),
            Policy(namespace = namespace,
                   permissions = self.policy_permissions(worker))
        ]

    def init_event_rule(self, parent_ns, event):
        child_ns = f"{parent_ns}-{event['name']}"
        self.append(Rule(namespace = child_ns,
                         function_namespace = parent_ns,
                         pattern = event["pattern"]))
        self.append(EventPermission(namespace = child_ns,
                                    function_namespace = parent_ns))
        
    def init_log_subscriptions(self, namespace, logging_namespace, worker, log_levels):
        for log_level in log_levels:
            child_logging_ns = f"{logging_namespace}-{log_level}"
            subscriptionfn = eval(H(f"{log_level}-subscription-filter"))
            self.append(subscriptionfn(namespace = namespace,
                                       logging_namespace = child_logging_ns))

    """
    - logs are created entirely in the logging namespace
    """
            
    def init_logs(self, parent_ns, log_levels):
        for log_level in log_levels:
            child_ns = f"{parent_ns}-{log_level}"
            self.append(SlackFunction(namespace = child_ns,
                                      log_level = log_level))
            self.append(SlackRole(namespace = child_ns))
            self.append(SlackPolicy(namespace = child_ns))
            self.append(SlackPermission(namespace = child_ns))
            
if __name__ == "__main__":
    pass

    
