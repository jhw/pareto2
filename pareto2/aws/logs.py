from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class SubscriptionFilter(Resource):
    
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

    @property
    def aws_properties(self):
        destination_arn = {"Fn::GetAtt": [H(f"{self.name}-logs-function"), "Arn"]}
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.name)}
        return {
            "DestinationArn": destination_arn,
            "FilterPattern": self.pattern,
            "LogGroupName": log_group_name
        }

    @property
    def depends(self):
        return [
            H(f"{self.name}-log-stream"),
            H(f"{self.name}-logs-permission")
        ]

class LogGroup(Resource):

    def __init__(self, name, retention_days=3):
        self.name = name
        self.retention_days = retention_days

    @property
    def aws_properties(self):
        # Assuming LogGroupPattern is a predefined pattern string
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.name)}
        return {
            "LogGroupName": log_group_name,
            "RetentionInDays": self.retention_days
        }

class LogStream(Resource):

    def __init__(self, name, retention_days=3):
        self.name = name
        self.retention_days = retention_days

    @property
    def aws_properties(self):
        # Assuming LogGroupPattern is a predefined pattern string
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.name)}
        return {
            "LogGroupName": log_group_name
        }

    @property
    def depends(self):
        return [H(f"{self.name}-log-group")]

