# Subclass for Streaming Role
class StreamingRole(FunctionBase):
    def __init__(self, table, permissions=None):
        super().__init__(table["name"], permissions or ["dynamodb:GetRecords", "dynamodb:GetShardIterator", "dynamodb:DescribeStream", "dynamodb:ListStreams", "events:PutEvents", "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"])
