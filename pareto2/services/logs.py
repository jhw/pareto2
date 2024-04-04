from pareto2.services import hungarorise as H
from pareto2.services import Resource

"""
- subscription filter needs separate function_namespace, alert_namespace arguments as its root namespace is a combination of both (since a single function might need multiple subscription filters)
- function_namespace is effectively the source (watches the log group, named after the function)
- alert_namespace is the destination, containing the alert function
"""

class SubscriptionFilter(Resource):

    def __init__(self, namespace, function_namespace, alert_namespace, filter_pattern):
        self.namespace = namespace
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

class Alarm(Resource):

    def __init__(self,
                 namespace,
                 alarm_namespace,
                 cloudwatch_namespace = "AWS/Lambda",
                 metric_name = "Invocations",
                 statistic = "Sum",
                 period = 60,
                 evaluation_periods = 1,
                 threshold = 10,
                 comparison_operator = "GreaterThanThreshold"):
        self.namespace = namespace
        self.alarm_namespace = alarm_namespace
        self.cloudwatch_namespace = cloudwatch_namespace
        self.metric_name = metric_name
        self.statistic = statistic
        self.period = period
        self.evaluation_periods = evaluation_periods
        self.threshold = threshold
        self.comparison_operator = comparison_operator

    @property
    def aws_properties(self):
        return {
            "Namespace": self.cloudwatch_namespace,
            "MetricName": self.metric_name,
            "Dimensions": [
                {
                    "Name": "FunctionName",
                    "Value": {"Ref": H(f"{self.namespace}-function")}
                }
            ],
            "Statistic": self.statistic,
            "Period": self.period,
            "EvaluationPeriods": self.evaluation_periods,
            "Threshold": self.threshold,
            "ComparisonOperator": self.comparison_operator,
            "AlarmActions": [
                {"Ref": H(f"{self.alarm_namespace}-topic")}
            ]
        }
    
"""
- LogGroup/LogStream namespace is function namespace
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

