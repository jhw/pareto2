from pareto2.services import hungarorise as H
from pareto2.services.events import *
from pareto2.services.iam import *
from pareto2.recipes import *
from pareto2.recipes.mixins.alarms import AlarmMixin
from pareto2.recipes.mixins.slackops import SlackMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

class EventPermission(L.Permission):

    def __init__(self, namespace, function_namespace):
        source_arn = {"Fn::GetAtt": [H(f"{namespace}-rule"), "Arn"]}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "events.amazonaws.com")

class EventWorker(AlarmMixin, SlackMixin):    

    def __init__(self,
                 namespace,
                 worker,
                 log_levels = ["warning", "error"]):
        super().__init__()
        self.init_worker(namespace = namespace,
                         worker = worker)
        self.init_alarm_hook(namespace = namespace,
                             alarm = worker["alarm"])
        self.init_slack_hooks(function_namespace = namespace,
                              log_levels = log_levels)
        self.init_alarm_resources()
        self.init_slack_resources()

    def init_worker(self, namespace, worker):
        fn = L.InlineFunction if "code" in worker else L.S3Function
        self += [fn(namespace = namespace,
                    **function_kwargs(worker)),
                 L.EventInvokeConfig(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace,
                        permissions = policy_permissions(worker)),
                 PatternRule(namespace = namespace,
                             pattern = worker["event"]["pattern"]),
                 EventPermission(namespace = namespace,
                                 function_namespace = namespace)]
        
if __name__ == "__main__":
    pass

    
