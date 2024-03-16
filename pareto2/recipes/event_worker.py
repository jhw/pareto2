from pareto2.recipes import Recipe

import importlib, re

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

LoggingNamespace = "logs"

class EventWorker(Recipe):    

    def __init__(self, namespace, logging_namespace = LoggingNamespace):
        super().__init__()
        for klass in [lambda_module.SlackWebhookFunction]:
            self.append(klass(namespace = logging_namespace))
            
if __name__ == "__main__":
    pass

    
