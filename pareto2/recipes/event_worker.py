from pareto2.recipes import Recipe

import importlib

slack_module = importlib.import_module("pareto2.ingredients.lambda.slack")

LoggingNamespace = "logs"

class EventWorker(Recipe):    

    def __init__(self, namespace, logging_namespace = LoggingNamespace):
        super().__init__()
        for klass in [slack_module.SlackWebhookFunction,
                      slack_module.SlackWebhookRole,
                      slack_module.SlackWebhookPermission]:
            self.append(klass(namespace = logging_namespace))
            
if __name__ == "__main__":
    pass

    
