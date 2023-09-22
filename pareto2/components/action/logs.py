from pareto2.components import hungarorise as H
from pareto2.components import resource

LogGroupPattern="/aws/lambda/${%s}" # note preceeding slash

@resource
def init_log_group(action, retentiondays=3):
    resourcename=H("%s-log-group" % action["name"])
    loggroupname={"Fn::Sub": LogGroupPattern % H("%s-function" % action["name"])}
    props={"LogGroupName": loggroupname,
           "RetentionInDays": retentiondays}
    return (resourcename,
            "AWS::Logs::LogGroup",
            props)

@resource
def init_log_stream(action, retentiondays=3):
    resourcename=H("%s-log-stream" % action["name"])
    loggroupname={"Fn::Sub": LogGroupPattern % H("%s-function" % action["name"])}
    props={"LogGroupName": loggroupname}
    depends=[H("%s-log-group" % action["name"])]
    return (resourcename,
            "AWS::Logs::LogStream",
            props,
            depends)

@resource
def init_logs_subscription(action, logs):
    resourcename=H("%s-%s-logs-subscription" % (action["name"],
                                                logs["name"]))
    destinationarn={"Fn::GetAtt": [H("%s-logs-function" % logs["name"]), "Arn"]}
    loggroupname={"Fn::Sub": LogGroupPattern % H("%s-function" % action["name"])}
    props={"DestinationArn": destinationarn,
           "FilterPattern": logs["pattern"],
           "LogGroupName": loggroupname}
    depends=[H("%s-log-stream" % action["name"]),
             H("%s-logs-permission" % logs["name"])]             
    return (resourcename,
            "AWS::Logs::SubscriptionFilter",
            props,
            depends)

def init_warn_logs_subscription(action):
    return init_logs_subscription(action, 
                                  logs={"name": "warn",
                                        "pattern": "WARNING"})

def init_error_logs_subscription(action):
    return init_logs_subscription(action, 
                                  logs={"name": "error",
                                        "pattern": "ERROR"})

if __name__=="__main__":
    pass
