from pareto2.services import hungarorise as H
from pareto2.services import Resource


"""
Unlike logs::SubscriptionFilter, Alarm - a resource which is very similar in nature - doesn't need a separate function_namespace field as you don't need to sub- namespace it with warning|error subscripts
"""

class Alarm(Resource):

    def __init__(self,
                 namespace,
                 alarm_namespace,
                 cloudwatch_namespace = "AWS/Lambda"):
        super().__init__(namespace)
        self.alarm_namespace = alarm_namespace
        self.cloudwatch_namespace = cloudwatch_namespace                 

    @property
    def aws_properties(self):
        return {
            "Namespace": self.cloudwatch_namespace,
            "Dimensions": [
                {
                    "Name": "FunctionName",
                    "Value": {"Ref": H(f"{self.namespace}-function")}
                }
            ],
            "AlarmActions": [
                {"Ref": H(f"{self.alarm_namespace}-topic")}
            ]
        }
        
class InvocationAlarm(Alarm):

    def __init__(self,
                 namespace,
                 alarm_namespace,
                 metric_name = "Invocations",
                 statistic = "Sum",
                 period = 60,
                 evaluation_periods = 1,
                 threshold = 10,
                 comparison_operator = "GreaterThanThreshold"):
        super().__init__(namespace = namespace,
                         alarm_namespace = alarm_namespace)
        self.metric_name = metric_name
        self.statistic = statistic
        self.period = period
        self.evaluation_periods = evaluation_periods
        self.threshold = threshold
        self.comparison_operator = comparison_operator

    @property
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "MetricName": self.metric_name,
            "Statistic": self.statistic,
            "Period": self.period,
            "EvaluationPeriods": self.evaluation_periods,
            "Threshold": self.threshold,
            "ComparisonOperator": self.comparison_operator
        })
        return props
    
