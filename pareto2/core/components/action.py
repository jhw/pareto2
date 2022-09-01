from pareto2.core.components import hungarorise as H
from pareto2.core.components import uppercase as U
from pareto2.core.components import resource

import re

DefaultPermissions={"logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"}

@resource            
def init_function(action):
    resourcename=H("%s-function" % action["name"])
    rolename=H("%s-function-role" % action["name"])
    memorysize=H("memory-size-%s" % action["size"])
    timeout=H("timeout-%s" % action["timeout"])
    code={"S3Bucket": {"Ref": H("artifacts-bucket")},
          "S3Key": {"Ref": H("artifacts-key")}}
    handler={"Fn::Sub": "%s/index.handler" % action["name"].replace("-", "/")}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": handler,
           "Runtime": runtime}
    if "packages" in action:
        props["Layers"]=[{"Ref": H("%s-layer-arn" % pkgname)}
                         for pkgname in action["packages"]]
    if "env" in action:
        variables={U(k): {"Ref": H(k)}
                   for k in action["env"]["variables"]}
        props["Environment"]={"Variables": variables}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_role(action, defaultpermissions=DefaultPermissions):
    def init_permissions(action, defaultpermissions):
        permissions=set(defaultpermissions)
        if "permissions" in action:
            permissions.update(set(action["permissions"]))
        return permissions        
    resourcename=H("%s-function-role" % action["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    permissions=init_permissions(action, defaultpermissions)
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(list(permissions))]}
    policyname={"Fn::Sub": "%s-function-role-policy-${AWS::StackName}" % action["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_event_config(action):
    resourcename=H("%s-function-event-config" % action["name"])
    retries=action["retries"] if "retries" in action else 0
    funcname=H("%s-function" % action["name"])
    destarn={"Fn::GetAtt": [H("%s-error-function" % action["name"]), "Arn"]}
    destconfig={"OnFailure": {"Destination": destarn}}
    props={"MaximumRetryAttempts": retries,
           "FunctionName": {"Ref": funcname},
           "Qualifier": "$LATEST",
           "DestinationConfig": destconfig}
    return (resourcename,
            "AWS::Lambda::EventInvokeConfig",
            props)

@resource
def _init_event_rule(action, event, pattern):
    def init_target(action, event):
        id={"Fn::Sub": "%s-%s-event-rule-${AWS::StackName}" % (action["name"],
                                                               event["name"])}
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
- event is custom event created by table-function
"""

def init_dynamodb_event_rule(action, event):
    pattern={"detail": event["pattern"]}
    pattern["source"]=[{"Ref": H("%s-table-function" % event["table"])}]
    return _init_event_rule(action, event, pattern)

"""
- event is created by s3 eventbridge notification config
"""

def init_s3_event_rule(action, event):
    pattern={"detail": event["pattern"]}
    pattern["detail"].setdefault("bucket", {})
    pattern["detail"]["bucket"]["name"]=[{"Ref": H("%s-bucket" % event["bucket"])}]
    pattern["source"]=["aws.s3"]
    return _init_event_rule(action, event, pattern)

def init_event_rule(action, event):
    fn=eval("init_%s_event_rule" % event["type"])
    return fn(action, event)

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

def init_async_component(action):
    resources=[]
    for fn in [init_function,
               init_role,
               init_event_config]:
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
               init_role]:
        resource=fn(action)
        resources.append(resource)
    return resources

def init_component(action):
    fn=eval("init_%s_component" % action["type"])
    return fn(action)

def init_resources(md):
    resources=[]
    for action in md["actions"]:
        component=init_component(action)
        resources+=component
    return dict(resources)

def update_template(template, md):
    template.resources.update(init_resources(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("actions")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
