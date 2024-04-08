from pareto2.services import hungarorise as H
from pareto2.services.iam import *
from pareto2.services.logs import *
from pareto2.recipes import *

import importlib

L = importlib.import_module("pareto2.services.lambda")

AlertNamespace = "alert"

class AlertFunction(L.InlineFunction):

    def __init__(self, namespace, log_level):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})

class AlertsMixin(Recipe):

    def __init__(self):
        super().__init__()

    def init_alert_hooks(self,
                         namespace,
                         log_levels,
                         alerts_namespace = AlertNamespace,
                         filter_patterns = {"warning": "%WARNING|Task timed out%",
                                            "error": "ERROR"}):
        self += [LogGroup(namespace = namespace),
                 LogStream(namespace = namespace)]
        for log_level in log_levels:
            filter_namespace = f"{namespace}-{log_level}"
            alert_namespace = f"{alerts_namespace}-{log_level}"
            self.append(SubscriptionFilter(namespace = filter_namespace,
                                           function_namespace = namespace,
                                           alert_namespace = alert_namespace,
                                           filter_pattern = filter_patterns[log_level]))

    @property
    def log_levels(self):
        return list(set([resource.resource_name.split("-")[-3]
                         for resource in self
                         if resource.aws_resource_type == "AWS::Logs::SubscriptionFilter"]))

    def init_alert_resources(self, namespace = AlertNamespace):
        for log_level in self.log_levels:
            alert_namespace = f"{namespace}-{log_level}"
            self += [AlertFunction(namespace = alert_namespace,
                                   log_level = log_level),
                     Role(namespace = alert_namespace),
                     Policy(namespace = alert_namespace),
                     L.Permission(namespace = alert_namespace,
                                  principal = "logs.amazonaws.com")]

