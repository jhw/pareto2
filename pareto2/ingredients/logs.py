from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import Resource

"""
- namespace here is always a function namespace
- each lambda must have its own subscription filters, log group, log stream
- but logging function is a singleton
"""

class SubscriptionFilter(Resource):

    def __init__(self, namespace, logging_namespace, filter_pattern):
        self.namespace = namespace
        self.logging_namespace = logging_namespace
        self.filter_pattern = filter_pattern

    @property
    def aws_properties(self):
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/{self.namespace}-function"}
        }

class WarningSubscriptionFilter(SubscriptionFilter):

    def __init__(self, namespace, logging_namespace, filter_pattern = "%WARNING|Task timed out%"):
        super().__init__(namespace = namespace,
                         logging_namespace = logging_namespace,
                         filter_pattern = filter_pattern)

class ErrorSubscriptionFilter(SubscriptionFilter):

    def __init__(self, namespace, logging_namespace, filter_pattern = "ERROR"):
        super().__init__(namespace = namespace,
                         logging_namespace = logging_namespace,
                         filter_pattern = filter_pattern)
            
class LogGroup(Resource):

    def __init__(self, namespace, retention_days = 3):
        self.namespace = namespace
        self.retention_days = retention_days

    @property
    def aws_properties(self):
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/{self.namespace}-function"},
            "RetentionInDays": retention_days
        }

class LogStream(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/{self.namespace}-function"}
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-log-group")]
