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
def init_role(action, **kwargs):
    def init_permissions(action,
                         defaultpermissions=DefaultPermissions):
        permissions=set(defaultpermissions)
        if "permissions" in action:
            permissions.update(set(action["permissions"]))
        return permissions        
    resourcename=H("%s-function-role" % action["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    permissions=init_permissions(action)
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
def _init_event_rule(action, event, detail):
    def init_target(action, event):
        id={"Fn::Sub": "%s-function-%s-event-rule-${AWS::StackName}" % (action["name"],
                                                                        event["name"])}
        arn={"Fn::GetAtt": [H("%s-function" % action["name"]), "Arn"]}
        return {"Id": id,
                "Arn": arn}
    resourcename=H("%s-function-%s-event-rule" % (action["name"],
                                                  event["name"]))
    pattern={"detail": detail}
    target=init_target(action, event)
    props={"EventPattern": pattern,
           "Targets": [target],
           "State": "ENABLED"}
    """
    if "router" in event:
        eventbusname={"Ref": H("%s-router-event-bus" % event["router"])}
        props["EventBusName"]=eventbusname
    """
    return (resourcename,
            "AWS::Events::Rule",
            props)

def init_dynamodb_event_rule(action, event):
    pattern={"detail": event["pattern"]}
    pattern["source"]=[{"Ref": H("%s-table-function" % event["table"])}]
    return pattern

def init_s3_event_rule(action, event):
    pattern={"detail": event["pattern"]}
    pattern["detail"]["bucket"]["name"]=[{"Ref": H("%s-bucket" % event["bucket"])}]
    return pattern

def init_codebuild_event_rule(action, event):
    pattern={"detail": event["pattern"]}
    return pattern

def init_event_rule(action, event):
    fn=eval("init_%s_event_rule" % event["type"])
    return fn(action, event)

@resource
def init_event_rule_permission(action, event):
    resourcename=H("%s-event-rule-permission" % event["name"])
    sourcearn={"Fn::GetAtt": [H("%s-event-rule" % event["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % action["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_component(action):
    resources=[]
    for fn in [init_function,
               init_role]:
        resource=fn(action)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for action in md.actions:
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
