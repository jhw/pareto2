import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class SlackWebhookFunction(lambda_module.InlineFunction):

    def __init__(self, namespace, **kwargs):
        super().__init__(namespace,
                         code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         **kwargs)
