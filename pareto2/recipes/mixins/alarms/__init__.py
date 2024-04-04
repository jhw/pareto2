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
    - namespace is alarm_namespace
    """
        
    def init_alarm_hook(self,
                        namespace,
                        function_namespace):
        self += [Alarm(namespace = namespace,
                       function_namespace = function_namespace)]
        
    """
    - namespace is alarm_namespace
    """

    def init_alarm_resources(self, namespace):
        self += [Topic(namespace = namespace),
                 Subscription(namespace = namespace),
                 AlarmFunction(namespace = namespace),
                 Role(namespace = namespace),
                 Policy(namespace = namespace),
                 L.Permission(namespace = namespace,
                              source_arn = {"Ref": H(f"{namespace}-topic")}, # NB returns an ARN
                              principal = "sns.amazonaws.com")]
