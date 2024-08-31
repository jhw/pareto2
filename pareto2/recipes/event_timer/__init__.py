from pareto2.services import hungarorise as H
from pareto2.services.events import *
from pareto2.services.iam import *
from pareto2.recipes import *

from pareto2.recipes.mixins.alerts import AlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

class EventPermission(L.Permission):

    def __init__(self, namespace):
        source_arn = {"Fn::GetAtt": [H(f"{namespace}-rule"), "Arn"]}
        super().__init__(namespace = namespace,    
                         source_arn = source_arn,
                         principal = "events.amazonaws.com")

class EventTimer(AlertsMixin):    

    def __init__(self,
                 namespace,
                 timer,
                 log_levels = ["warning", "error"]):
        super().__init__()
        self.init_timer(namespace = namespace,
                         timer = timer)
        self.init_alert_hooks(namespace = namespace,
                              log_levels = log_levels)
        self.init_alert_resources()

    def init_timer(self, namespace, timer):
        fn = L.InlineFunction if "code" in timer else L.S3Function
        self += [fn(namespace = namespace,
                    **function_kwargs(timer)),
                 L.EventInvokeConfig(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace,
                        permissions = policy_permissions(timer)),
                 TimerRule(namespace = namespace,
                           rate = timer["event"]["rate"]),
                 EventPermission(namespace = namespace)]
        
if __name__ == "__main__":
    pass

    
