from pareto2.services import hungarorise as H
from pareto2.services import Resource

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
        function_ref = H(f"{self.namespace}-function")
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/${{{function_ref}}}"},
            "FilterPattern": self.filter_pattern,
            "DestinationArn": {"Fn::GetAtt": [H(f"{self.logging_namespace}-function"), "Arn"]},
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-log-stream"),
                H(f"{self.logging_namespace}-permission")]

    
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

"""
- LogGroup and LogStream don't seem to need explicit refs to their parent function; must be connected implicitly via the LogGroupName (which contains function name)
"""
        
class LogGroup(Resource):

    def __init__(self, namespace, retention_days = 3):
        self.namespace = namespace
        self.retention_days = retention_days

    @property
    def aws_properties(self):
        function_ref = H(f"{self.namespace}-function")
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/${{{function_ref}}}"},
            "RetentionInDays": self.retention_days
        }

class LogStream(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        function_ref = H(f"{self.namespace}-function")
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/${{{function_ref}}}"}
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-log-group")]
