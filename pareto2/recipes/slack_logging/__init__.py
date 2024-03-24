from pareto2.services import hungarorise as H

from pareto2.services.iam import *

from pareto2.recipes import Recipe

import importlib

L = importlib.import_module("pareto2.services.lambda")

"""
- NB slack-webhook-url defined declaratively / as a Ref, so appears as a top level Parameter
- remember one Slack webhook per application
"""

class SlackFunction(L.InlineFunction):

    def __init__(self, namespace, log_level):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})
    
class SlackLoggingRecipe(Recipe):

    def __init__(self):
        super().__init__()

    @property
    def log_levels(self):
        return list(set([resource.resource_name.split("-")[-3]
                         for resource in self
                         if resource.aws_resource_type == "AWS::Logs::SubscriptionFilter"]))
                
    """
    - logs are created entirely in the logging namespace
    """
            
    def init_slack_logs(self, parent_ns):
        for log_level in self.log_levels:
            child_ns = f"{parent_ns}-{log_level}"
            self.append(SlackFunction(namespace = child_ns,
                                      log_level = log_level))
            self.append(Role(namespace = child_ns))
            self.append(Policy(namespace = child_ns))
            self.append(L.Permission(namespace = child_ns,
                                                 principal = "logs.amazonaws.com"))

