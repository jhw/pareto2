from pareto2.services import hungarorise as H
from pareto2.services import Resource

"""
- subscription filter needs separate function_namespace, alert_namespace arguments as its root namespace is a combination of both (since a single function might need multiple subscription filters)
- function_namespace is effectively the source (watches the log group, named after the function)
- alert_namespace is the destination, containing the alert function
"""

class SubscriptionFilter(Resource):

    def __init__(self, namespace, function_namespace, alert_namespace, filter_pattern):
        super().__init__(namespace)
        self.function_namespace = function_namespace
        self.alert_namespace = alert_namespace
        self.filter_pattern = filter_pattern

    @property
    def aws_properties(self):
        function_ref = H(f"{self.function_namespace}-function")
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/${{{function_ref}}}"},
            "FilterPattern": self.filter_pattern,
            "DestinationArn": {"Fn::GetAtt": [H(f"{self.alert_namespace}-function"), "Arn"]},
        }

    @property
    def depends(self):
        return [H(f"{self.function_namespace}-log-stream"),
                H(f"{self.alert_namespace}-permission")]

"""
- LogGroup/LogStream namespace is function namespace
"""
        
class LogGroup(Resource):

    def __init__(self, namespace, retention_days = 3):
        super().__init__(namespace)
        self.retention_days = retention_days

    @property
    def aws_properties(self):
        function_ref = H(f"{self.namespace}-function")
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/${{{function_ref}}}"},
            "RetentionInDays": self.retention_days
        }

class LogStream(Resource):

    @property
    def aws_properties(self):
        function_ref = H(f"{self.namespace}-function")
        return {
            "LogGroupName": {"Fn::Sub": f"/aws/lambda/${{{function_ref}}}"}
        }

    @property
    def depends(self):
        return [H(f"{self.namespace}-log-group")]

