from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.iam import Role, Policy

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

"""
- NB slack-webhook-url defined declaratively / as a Ref, so appears as a top level Parameter
- remember one Slack webhook per application
"""

class SlackWebhookFunction(lambda_module.InlineFunction):

    def __init__(self, namespace, log_level):
        super().__init__(namespace = namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})

class SlackWebhookRole(Role):

    def __init__(self, namespace):
        super().__init__(namespace = namespace)
        
class SlackWebhookPolicy(Policy):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         permissions = ["logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"])

class SlackWebhookPermission(lambda_module.Permission):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         principal = "logs.amazonaws.com")

