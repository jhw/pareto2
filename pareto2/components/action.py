from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

import random, re

AsyncPermissions={"logs:CreateLogGroup",
                  "logs:CreateLogStream",
                  "logs:PutLogEvents"}

"""
- sync action is most commonly bound to sqs
"""

SyncPermissions={"logs:CreateLogGroup",
                 "logs:CreateLogStream",
                 "logs:PutLogEvents",                 
                 "sqs:DeleteMessage",
                 "sqs:GetQueueAttributes",
                 "sqs:ReceiveMessage"}

FunctionDefaults={"size": "small",
                  "timeout": "short"}

def function_defaults(fn):
    def wrapped(action, defaults=FunctionDefaults):
        for k, v in defaults.items():
            if k not in action:
                action[k]=v
        return fn(action)
    return wrapped

@function_defaults
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
    if "layers" in action:
        props["Layers"]=[{"Ref": H("%s-layer-arn" % pkgname)}
                         for pkgname in action["layers"]]
    if "env" in action:
        def format_env_ref(k):
            if k.lower().endswith("arn"):
                k2="-".join([tok for tok in re.split("\\-|\\_", k)
                             if tok!=''][:-1])
                return (U(k), {"Fn::GetAtt": [H(k2), "Arn"]})
            else:
                return (U(k), {"Ref": H(k)})
        variables=dict([format_env_ref(k)
                        for k in action["env"]["variables"]])
        props["Environment"]={"Variables": variables}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_function_role(action, basepermissions):
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

def init_async_function_role(action, permissions=AsyncPermissions):
    return init_function_role(action, basepermissions=permissions)

def init_sync_function_role(action, permissions=SyncPermissions):
    return init_function_role(action, basepermissions=permissions)

@resource
def init_async_function_event_config(action, retries=0):
    resourcename=H("%s-function-event-config" % action["name"])
    funcname=H("%s-function" % action["name"])
    props={"MaximumRetryAttempts": retries,
           "FunctionName": {"Ref": funcname},
           "Qualifier": "$LATEST"}
    return (resourcename,
            "AWS::Lambda::EventInvokeConfig",
            props)

"""
- event rule uses random slug in id because of max length 64
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-events-rule-target.html#cfn-events-rule-target-id
- problem is combination of action.name + event.name + AWS::StackName can often exceed 64 chars, and there is no Fn::Substring function to put a ceiling on it
"""

@resource
def _init_event_rule(action, event, pattern):
    def random_id(n=16):
        return "".join([chr(65+int(26*random.random()))
                        for i in range(n)])
    def init_target(action, event):
        """
        id={"Fn::Sub": "%s-%s-event-rule-${AWS::StackName}" % (action["name"],
                                                               event["name"])}
        """
        id={"Fn::Sub": "%s-${AWS::StackName}" % random_id(n=8)}
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

def init_async_component(action):
    resources=[]
    for fn in [init_function,
               init_async_function_role,
               init_async_function_event_config]:
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
               init_sync_function_role]:
        resource=fn(action)
        resources.append(resource)
    return resources

def render_resources(action):
    fn=eval("init_%s_component" % action["invocation-type"])
    return dict(fn(action))

def render_outputs(action):
    return {}

if __name__=="__main__":
    try:
        import os, sys
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        from pareto2.dsl import Config
        config=Config.init_file(filename=filename)
        from pareto2.template import Template
        template=Template()
        for action in config["components"].actions:
            template.resources.update(render_resources(action))
            template.outputs.update(render_outputs(action))
        print (template.render())
    except RuntimeError as error:
        print ("Error: %s" % str(error))
