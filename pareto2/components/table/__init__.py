from pareto2.aws.dynamodb import Table as TableBase

from pareto.aws.iam import Role as RoleBase

from pareto.aws.lambda import EventSourceMapping
from pareto.aws.lambda import Function as FunctionBase

class Table(TableBase):
    
    def __init__(self, table, streamtype="NEW_AND_OLD_IMAGES", **kwargs):
        super().__init__(table, streamtype, **kwargs)

class StreamingFunction(FunctionBase):

    def __init__(self, table,
                 batchsize=StreamBatchSize,
                 code=FunctionCode):
        envvars = {
            "batch-size": str(batchsize),
            "debug": str(table["streaming"].get("debug", "false"))
        }
        super().__init__(
            name=table["name"],
            role_suffix="table-streaming-function-role",
            code={"ZipFile": code},
            size=table["streaming"]["size"],
            timeout=table["streaming"]["timeout"],
            envvars={k: {"Ref": v} for k, v in envvars.items()}
        )
        self.handler = "index.handler"

    @property
    def resource_name(self):
        return f"{self.name}-table-streaming-function"

class StreamingRole(RoleBase):

    def __init__(self, table, permissions=None):
        super().__init__(table["name"],
                         permissions or ["dynamodb:GetRecords",
                                         "dynamodb:GetShardIterator",
                                         "dynamodb:DescribeStream",
                                         "dynamodb:ListStreams",
                                         "events:PutEvents",
                                         "logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents"])

class StreamingBinding(EventSourceMapping):
    
    def __init__(self, table, stream_window=StreamWindow, stream_retries=StreamRetries):
        super().__init__(
            name=f"{table['name']}-table-mapping",
            function_ref=f"{table['name']}-table-streaming-function",
            source_arn={"Fn::GetAtt": [f"{table['name']}-table", "StreamArn"]},
            starting_position="LATEST",
            maximum_batching_window_in_seconds=stream_window,
            maximum_retry_attempts=stream_retries
        )
