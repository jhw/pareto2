from pareto2.services import hungarorise as H

from pareto2.services.events import *
from pareto2.services.iam import *

from pareto2.recipes.mixins.slackops import SlackAlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

class EventPermission(L.Permission):

    def __init__(self, namespace, function_namespace):
        source_arn = {"Fn::GetAtt": [H(f"{namespace}-rule"), "Arn"]}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "events.amazonaws.com")

class EventWorker(SlackAlertsMixin):    

    def __init__(self,
                 namespace,
                 worker,
                 alerts_namespace = "slack",
                 log_levels = ["warning", "error"]):
        super().__init__()
        self.init_worker(namespace = namespace,
                         worker = worker)
        self.init_subscription_filters(function_namespace = namespace,
                                       alerts_namespace = alerts_namespace,
                                       log_levels = log_levels)
        self.init_slackops(namespace = alerts_namespace)

    def init_worker(self, namespace, worker):
        self.append(self.init_function(namespace = namespace,
                                       worker = worker))
        self.append(L.EventInvokeConfig(namespace = namespace))
        self += self.init_role_and_policy(namespace = namespace,
                                          worker = worker)
        for event in worker["events"]:
            self.init_event_rule(namespace = namespace,
                                 event = event)
        
    def init_function(self, namespace, worker):
        fn = L.InlineFunction if "code" in worker else L.S3Function
        return (fn(namespace = namespace,
                   **self.function_kwargs(worker)))
    
    def init_role_and_policy(self, namespace, worker):
        return  [
            Role(namespace = namespace),
            Policy(namespace = namespace,
                   permissions = self.policy_permissions(worker))
        ]

    def init_event_rule(self, namespace, event):
        event_namespace = f"{namespace}-{event['name']}"
        self.append(Rule(namespace = event_namespace,
                         function_namespace = namespace,
                         pattern = event["pattern"]))
        self.append(EventPermission(namespace = event_namespace,
                                    function_namespace = namespace))
                    
if __name__ == "__main__":
    pass

    
