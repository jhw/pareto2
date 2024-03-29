from pareto2.services import hungarorise as H

from pareto2.services.iam import *
from pareto2.services.logs import *

from pareto2.recipes import Recipe

import importlib

L = importlib.import_module("pareto2.services.lambda")

class SlackFunction(L.InlineFunction):

    def __init__(self, namespace, log_level):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})
    
class SlackRecipe(Recipe):

    def __init__(self):
        super().__init__()

    def init_logs_subscriptions(self, namespace, logging_namespace, log_levels):
        self.append(LogGroup(namespace = namespace))
        self.append(LogStream(namespace = namespace))
        for log_level in log_levels:
            child_logging_ns = f"{logging_namespace}-{log_level}"
            subscriptionfn = eval(H(f"{log_level}-subscription-filter"))
            self.append(subscriptionfn(namespace = namespace,
                                       logging_namespace = child_logging_ns))

    @property
    def log_levels(self):
        return list(set([resource.resource_name.split("-")[-3]
                         for resource in self
                         if resource.aws_resource_type == "AWS::Logs::SubscriptionFilter"]))

    def init_slack_logs(self, namespace):
        for log_level in self.log_levels:
            child_ns = f"{namespace}-{log_level}"
            self.append(SlackFunction(namespace = child_ns,
                                      log_level = log_level))
            self.append(Role(namespace = child_ns))
            self.append(Policy(namespace = child_ns))
            self.append(L.Permission(namespace = child_ns,
                                                 principal = "logs.amazonaws.com"))

