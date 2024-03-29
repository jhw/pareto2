from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

from pareto2.components.action.events import init_event_rule, init_event_rule_permission
from pareto2.components.action.logs import init_log_group, init_log_stream, init_warn_logs_subscription, init_error_logs_subscription

from pareto2.components.common.iam import policy_document, assume_role_policy_document

BasePermissions={"logs:CreateLogGroup",
                 "logs:CreateLogStream",
                 "logs:PutLogEvents"}

ActionDefaults={"size": "default",
                "timeout": "default",
                "invocation-type": "async"}

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
    resourcename=H("%s-function-role" % action["name"])
    policyname={"Fn::Sub": "%s-function-role-policy-${AWS::StackName}" % action["name"]}
    policydoc=policy_document(init_permissions(action, basepermissions))
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
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
- warn logs currenty commented out as CloudWatch seems to have trouble with two subscription filters
"""

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
               init_warn_logs_subscription,
               init_error_logs_subscription]:
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
