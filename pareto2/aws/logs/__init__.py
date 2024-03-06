class SubscriptionFilter:
    
    def __init__(self, action, logs):
        self.action = action
        self.logs = logs

    @property
    def resource_name(self):
        return f"{self.action['name']}-{self.logs['name']}-logs-subscription"

    @property
    def aws_resource_type(self):
        return "AWS::Logs::SubscriptionFilter"

    @property
    def aws_properties(self):
        destination_arn = {"Fn::GetAtt": [f"{self.logs['name']}-logs-function", "Arn"]}
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.action['name'])}
        return {
            "DestinationArn": destination_arn,
            "FilterPattern": self.logs["pattern"],
            "LogGroupName": log_group_name
        }

    @property
    def depends(self):
        return [
            f"{self.action['name']}-log-stream",
            f"{self.logs['name']}-logs-permission"
        ]

class LogsSubscription(LogsSubscriptionBase):
    def __init__(self, action, logs):
        super().__init__(action, logs)


class LogGroup:

    def __init__(self, action, retention_days=3):
        self.action = action
        self.retention_days = retention_days

    @property
    def resource_name(self):
        return f"{self.action['name']}-log-group"

    @property
    def aws_resource_type(self):
        return "AWS::Logs::LogGroup"

    @property
    def aws_properties(self):
        # Assuming LogGroupPattern is a predefined pattern string
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.action['name'])}
        return {
            "LogGroupName": log_group_name,
            "RetentionInDays": self.retention_days
        }

class LogStream:

    def __init__(self, action, retention_days=3):
        self.action = action
        self.retention_days = retention_days

    @property
    def resource_name(self):
        return f"{self.action['name']}-log-stream"

    @property
    def aws_resource_type(self):
        return "AWS::Logs::LogStream"

    @property
    def aws_properties(self):
        # Assuming LogGroupPattern is a predefined pattern string
        log_group_name = {"Fn::Sub": LogGroupPattern.format(self.action['name'])}
        return {
            "LogGroupName": log_group_name
        }

    @property
    def depends(self):
        return [f"{self.action['name']}-log-group"]

