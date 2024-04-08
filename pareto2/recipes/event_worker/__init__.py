from pareto2.services import hungarorise as H
from pareto2.services.events import *
from pareto2.services.iam import *
from pareto2.services.sns import *
from pareto2.recipes import *
from pareto2.recipes.mixins.alarms import AlarmsMixin
from pareto2.recipes.mixins.alerts import AlertsMixin

import importlib

L = importlib.import_module("pareto2.services.lambda")

class RulePermission(L.Permission):

    def __init__(self, namespace):
        source_arn = {"Fn::GetAtt": [H(f"{namespace}-rule"), "Arn"]}
        super().__init__(namespace = namespace,    
                         source_arn = source_arn,
                         principal = "events.amazonaws.com")

class TopicPermission(L.Permission):

    def __init__(self, namespace):
        source_arn = {"Ref": H(f"{namespace}-topic")}
        super().__init__(namespace = namespace,    
                         source_arn = source_arn,
                         principal = "sns.amazonaws.com")
        
class EventWorker(AlarmsMixin, AlertsMixin):    

    def __init__(self,
                 namespace,
                 worker,
                 log_levels = ["warning", "error"]):
        super().__init__()
        workerfn = self.init_event_worker if "event" in worker else self.init_topic_worker
        workerfn(namespace = namespace,
                 worker = worker)
        self.init_alarm_hook(namespace = namespace,
                             alarm = worker["alarm"])
        self.init_alert_hooks(namespace = namespace,
                              log_levels = log_levels)
        self.init_alarm_resources()
        self.init_alert_resources()

    def init_event_worker(self, namespace, worker):
        fn = L.InlineFunction if "code" in worker else L.S3Function
        self += [fn(namespace = namespace,
                    **function_kwargs(worker)),
                 L.EventInvokeConfig(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace,
                        permissions = policy_permissions(worker)),
                 PatternRule(namespace = namespace,
                             pattern = worker["event"]["pattern"]),
                 RulePermission(namespace = namespace)]

    def init_topic_worker(self, namespace, worker):
        fn = L.InlineFunction if "code" in worker else L.S3Function
        self += [fn(namespace = namespace,
                    **function_kwargs(worker)),
                 L.EventInvokeConfig(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace,
                        permissions = policy_permissions(worker)),
                 Topic(namespace = namespace),
                 TopicPermission(namespace = namespace)]

        
if __name__ == "__main__":
    pass

    
