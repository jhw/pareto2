from pareto2.ingredients.iam import Role

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class SlackWebhookFunction(lambda_module.InlineFunction):

    def __init__(self, namespace, log_level, **kwargs):
        super().__init__(namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         variables = {"slack-logging-level": log_level},
                         **kwargs)

class SlackWebhookRole(Role):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         permissions = ["logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents"])

class SlackWebhookPermission(lambda_module.Permission):

    def __init__(self, namespace):
        super().__init__(namespace,
                         function_namespace = namespace,
                         principal = "logs.amazon.com")

