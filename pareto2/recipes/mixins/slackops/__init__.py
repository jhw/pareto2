from pareto2.services import hungarorise as H

from pareto2.services.iam import *
from pareto2.services.logs import *

from pareto2.recipes import Recipe

import importlib

L = importlib.import_module("pareto2.services.lambda")

class SlackFunction(L.InlineFunction):

    def __init__(self, namespace, log_level):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})

class SlackAlertsMixin(Recipe):

    def __init__(self):
        super().__init__()

    def init_subscription_filters(self,
                                  function_namespace,
                                  alerts_namespace,
                                  log_levels,
                                  filter_patterns = {"warning": "%WARNING|Task timed out%",
                                                     "error": "ERROR"}):
        self.append(LogGroup(namespace = function_namespace))
        self.append(LogStream(namespace = function_namespace))
        for log_level in log_levels:
            filter_namespace = f"{function_namespace}-{log_level}"
            alert_namespace = f"{alerts_namespace}-{log_level}"
            self.append(SubscriptionFilter(namespace = filter_namespace,
                                           function_namespace = function_namespace,
                                           alert_namespace = alert_namespace,
                                           filter_pattern = filter_patterns[log_level]))

    @property
    def log_levels(self):
        return list(set([resource.resource_name.split("-")[-3]
                         for resource in self
                         if resource.aws_resource_type == "AWS::Logs::SubscriptionFilter"]))

    def init_slackops(self, namespace):
        for log_level in self.log_levels:
            alert_namespace = f"{namespace}-{log_level}"
            self.append(SlackFunction(namespace = alert_namespace,
                                      log_level = log_level))
            self.append(Role(namespace = alert_namespace))
            self.append(Policy(namespace = alert_namespace))
            self.append(L.Permission(namespace = alert_namespace,
                                                 principal = "logs.amazonaws.com"))
