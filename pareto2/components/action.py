from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

import re

BasePermissions={"logs:CreateLogGroup",
                 "logs:CreateLogStream",
                 "logs:PutLogEvents"}

ActionDefaults={"size": "default",
                "timeout": "default",
                "invocation-type": "async"}

LogGroupPattern="/aws/lambda/${%s}" # note preceeding slash

@resource            
def init_function(action):    
    resourcename=H("%s-function" % action["name"])
    rolename=H("%s-function-role" % action["name"])
    memorysize=H("memory-size-%s" % action["size"])
    timeout=H("timeout-%s" % action["timeout"])
    code={"S3Bucket": {"Ref": H("artifacts-bucket")},
          "S3Key": {"Ref": H("artifacts-key")}}
    handler={"Fn::Sub": "%s/index.handler" % action["path"].replace("-", "/")}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": handler,
           "Runtime": runtime}
    if "layers" in action:
        props["Layers"]=[{"Ref": H("%s-layer-arn" % pkgname)}
                         for pkgname in action["layers"]]
    if "env" in action:
        variables={U(k): {"Ref": H(k)}
                   for k in action["env"]["variables"]}
        props["Environment"]={"Variables": variables}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_function_role(action, basepermissions=BasePermissions):
    def init_permissions(action, basepermissions):
        permissions=set(basepermissions)
        if "permissions" in action:
            permissions.update(set(action["permissions"]))
        return sorted(list(permissions))
    class Group(list):
        def __init__(self, key, item=[]):
            list.__init__(item)
            self.key=key
        def render(self):
            return ["%s:*" % self.key] if "*" in self else ["%s:%s" % (self.key, value) for value in self]
    def group_permissions(permissions):
        groups={}
        for permission in permissions:
            prefix, suffix = permission.split(":")
            groups.setdefault(prefix, Group(prefix))
            groups[prefix].append(suffix)
        return [group.render()
                for group in list(groups.values())]
    resourcename=H("%s-function-role" % action["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    permissions=init_permissions(action, basepermissions)
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : group,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for group in group_permissions(permissions)]}
    policyname={"Fn::Sub": "%s-function-role-policy-${AWS::StackName}" % action["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_function_event_config(action, retries=0):
    resourcename=H("%s-function-event-config" % action["name"])
    funcname=H("%s-function" % action["name"])
    props={"MaximumRetryAttempts": retries,
           "FunctionName": {"Ref": funcname},
           "Qualifier": "$LATEST"}
    return (resourcename,
            "AWS::Lambda::EventInvokeConfig",
            props)

"""
- event rule target id max length 64
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-events-rule-target.html#cfn-events-rule-target-id
- don't introduce random elements in ids because this means rules will be deleted and recreated every time a stack deploys!
"""

@resource
def _init_event_rule(action, event, pattern, nmax=64):
    def init_target(action, event):
        id="%s-%s-target" % (action["name"],
                             event["name"])[:nmax] # NB
        arn={"Fn::GetAtt": [H("%s-function" % action["name"]), "Arn"]}
        return {"Id": id,
                "Arn": arn}
    resourcename=H("%s-%s-event-rule" % (action["name"],
                                         event["name"]))
    target=init_target(action, event)
    props={"EventPattern": pattern,
           "Targets": [target],
           "State": "ENABLED"}
    return (resourcename,
            "AWS::Events::Rule",
            props)

"""
- event is custom event created by table-streaming-function
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-events-rule-target.html#cfn-events-rule-target-id
"""

def init_table_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=event["topic"]
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    if "source" in event:
        pattern["source"]=[{"Ref": H("%s-table-streaming-function" % event["source"]["name"])}]
    if pattern=={}:
        raise RuntimeError("%s/%s event config is blank" % (action["name"],
                                                            event["name"]))
    return _init_event_rule(action, event, pattern)

"""
- event is created by s3 eventbridge notification config
"""

def init_bucket_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=event["topic"]
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    if "source" in event:
        pattern.setdefault("detail", {})
        pattern["detail"].setdefault("bucket", {})
        pattern["detail"]["bucket"]["name"]=[{"Ref": H("%s-bucket" % event["source"]["name"])}]
        pattern["source"]=["aws.s3"]
    if pattern=={}:
        raise RuntimeError("%s/%s event config is blank" % (action["name"],
                                                            event["name"]))
    return _init_event_rule(action, event, pattern)

def init_event_rule(action, event):
    if event["source"]["type"]=="bucket":
        return init_bucket_event_rule(action, event)
    elif event["source"]["type"]=="table":
        return init_table_event_rule(action, event)
    else:
        raise RuntimeError("no event rule handler for type %s" % event["type"])

@resource
def init_event_rule_permission(action, event):
    resourcename=H("%s-%s-event-rule-permission" % (action["name"],
                                                    event["name"]))
    sourcearn={"Fn::GetAtt": [H("%s-%s-event-rule" % (action["name"],
                                                      event["name"])), "Arn"]}
    funcname={"Ref": H("%s-function" % action["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

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
                                        "pattern": "WARN"})

def init_error_logs_subscription(action):
    return init_logs_subscription(action, 
                                  logs={"name": "error",
                                        "pattern": "ERROR"})

def init_async_component(action):
    resources=[]
    for fn in [init_function,
               init_function_role,
               init_function_event_config,
               init_log_group,
               init_log_stream,
               init_warn_logs_subscription,
               init_error_logs_subscription]:
        resource=fn(action)
        resources.append(resource)
    if "events" in action:
        for event in action["events"]:
            for fn in [init_event_rule,
                       init_event_rule_permission]:
                resource=fn(action, event)
                resources.append(resource)
    return resources

def init_sync_component(action):
    resources=[]
    for fn in [init_function,
               init_function_role,
               init_log_group,
               init_log_stream,
               init_logs_subscription]:
        resource=fn(action)
        resources.append(resource)
    return resources

def action_defaults(fn):
    def wrapped(action, defaults=ActionDefaults):
        for k, v in defaults.items():
            if k not in action:
                action[k]=v
        return fn(action)
    return wrapped

@action_defaults
def render_resources(action):
    fn=eval("init_%s_component" % action["invocation-type"])
    return dict(fn(action))

def render_outputs(action):
    return {}

if __name__=="__main__":
    pass
