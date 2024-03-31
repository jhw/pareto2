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

"""
- distinguish between logs_namespace (slack) and logging_namespace (eg slack-error)
"""
        
class SlackLogsMixin(Recipe):

    def __init__(self):
        super().__init__()

    def init_logs_subscriptions(self, namespace, logs_namespace, log_levels):
        self.append(LogGroup(namespace = namespace))
        self.append(LogStream(namespace = namespace))
        for log_level in log_levels:
            logging_namespace = f"{logs_namespace}-{log_level}"
            subscriptionfn = eval(H(f"{log_level}-subscription-filter"))
            self.append(subscriptionfn(namespace = namespace,
                                       logging_namespace = logging_namespace))

    @property
    def log_levels(self):
        return list(set([resource.resource_name.split("-")[-3]
                         for resource in self
                         if resource.aws_resource_type == "AWS::Logs::SubscriptionFilter"]))

    def init_slack_logs(self, namespace):
        for log_level in self.log_levels:
            logging_namespace = f"{namespace}-{log_level}"
            self.append(SlackFunction(namespace = logging_namespace,
                                      log_level = log_level))
            self.append(Role(namespace = logging_namespace))
            self.append(Policy(namespace = logging_namespace))
            self.append(L.Permission(namespace = logging_namespace,
                                                 principal = "logs.amazonaws.com"))

