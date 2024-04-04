from pareto2.services import hungarorise as H

from pareto2.services.iam import *
from pareto2.services.logs import *
from pareto2.services.sns import *

from pareto2.recipes import *

import importlib

L = importlib.import_module("pareto2.services.lambda")

class AlarmFunction(L.InlineFunction):

    def __init__(self, namespace, log_level):
        with open("/".join(__file__.split("/")[:-1]+["inline_code.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code)

class AlarmMixin(Recipe):

    def __init__(self):
        super().__init__()

    """
        self += [LogGroup(namespace = function_namespace),
                 LogStream(namespace = function_namespace)]
        for log_level in log_levels:
            filter_namespace = f"{function_namespace}-{log_level}"
            alert_namespace = f"{alerts_namespace}-{log_level}"
            self.append(SubscriptionFilter(namespace = filter_namespace,
                                           function_namespace = function_namespace,
                                           alert_namespace = alert_namespace,
                                           filter_pattern = filter_patterns[log_level]))
    """
        
    def init_alarm_hooks(self,
                         function_namespace,
                         alerts_namespace):
        pass
        
    """
    - namespace is alarm_namespace
    """
    
    def init_alarm_resources(self, namespace):
        self += [Topic(namespace = namespace),
                 AlarmFunction(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace),
                 L.Permission(namespace =namespace,
                              principal = "logs.amazonaws.com")]
