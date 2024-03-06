class SubscriptionFilter:
    
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

    @property
    def resource_name(self):
        return f"{self.name}-logs-subscription"

    @property
    def aws_resource_type(self):
        return "AWS::Logs::SubscriptionFilter"

    @property
    def aws_properties(self):
        destination_arn = {"Fn::GetAtt": [f"{self.name}-logs-function", "Arn"]}
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.name)}
        return {
            "DestinationArn": destination_arn,
            "FilterPattern": self.pattern,
            "LogGroupName": log_group_name
        }

    @property
    def depends(self):
        return [
            f"{self.name}-log-stream",
            f"{self.name}-logs-permission"
        ]

class LogGroup:

    def __init__(self, name, retention_days=3):
        self.name = name
        self.retention_days = retention_days

    @property
    def resource_name(self):
        return f"{self.name}-log-group"

    @property
    def aws_resource_type(self):
        return "AWS::Logs::LogGroup"

    @property
    def aws_properties(self):
        # Assuming LogGroupPattern is a predefined pattern string
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.name)}
        return {
            "LogGroupName": log_group_name,
            "RetentionInDays": self.retention_days
        }

class LogStream:

    def __init__(self, name, retention_days=3):
        self.name = name
        self.retention_days = retention_days

    @property
    def resource_name(self):
        return f"{self.name}-log-stream"

    @property
    def aws_resource_type(self):
        return "AWS::Logs::LogStream"

    @property
    def aws_properties(self):
        # Assuming LogGroupPattern is a predefined pattern string
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.name)}
        return {
            "LogGroupName": log_group_name
        }

    @property
    def depends(self):
        return [f"{self.name}-log-group"]

