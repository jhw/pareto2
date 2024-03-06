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
