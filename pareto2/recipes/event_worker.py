from pareto2.recipes import Recipe

import importlib

slack_module = importlib.import_module("pareto2.ingredients.lambda.slack")

"""
- LogNamespace is a singleton namespace 
"""

LogNamespace, LogLevels = "logs", ["warning", "error"]

class EventWorker(Recipe):    

    def __init__(self, namespace, logging_namespace = LogNamespace):
        super().__init__()
        self.init_logs(parent_ns = logging_namespace)

    def init_logs(self, parent_ns, log_levels = LogLevels):
        for log_level in log_levels:
            child_ns = f"{parent_ns}-{log_level}"
            self.append(slack_module.SlackWebhookFunction(namespace = child_ns,
                                                          log_level = log_level))
            self.append(slack_module.SlackWebhookRole(namespace = child_ns))
            self.append(slack_module.SlackWebhookPermission(namespace = child_ns))
            
if __name__ == "__main__":
    pass

    
