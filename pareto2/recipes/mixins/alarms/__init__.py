from pareto2.services import hungarorise as H
from pareto2.services.iam import *
from pareto2.services.logs import *
from pareto2.services.sns import *
from pareto2.recipes import *

import importlib

L = importlib.import_module("pareto2.services.lambda")

AlarmNamespace = "alarm"

"""
Alarm can't simply log warnings and expect these to be picked up by alerts code as Alarm lambda doesn't have any subscription filters attached; needs to push directly to Slack
"""

class AlarmFunction(L.InlineFunction):

    def __init__(self, namespace, log_level = "warning"):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})

class AlarmsMixin(Recipe):

    def __init__(self):
        super().__init__()

    def init_alarm_hook(self,
                        namespace,
                        alarm,
                        alarm_namespace = AlarmNamespace):        
        self += [InvocationAlarm(namespace = namespace,
                                 alarm_namespace = alarm_namespace,
                                 period = alarm["period"],
                                 threshold = alarm["threshold"])]
        
    def init_alarm_resources(self, namespace = AlarmNamespace):
        self += [Topic(namespace = namespace),
                 Subscription(namespace = namespace),
                 AlarmFunction(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace),
                 L.Permission(namespace = namespace,
                              source_arn = {"Ref": H(f"{namespace}-topic")}, # NB returns an ARN
                              principal = "sns.amazonaws.com")]
