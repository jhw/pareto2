from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import uppercase as U
from pareto2.cdk.components import resource

import re

"""
- events because it's an event driven system
- logs because everything always needs logs
- sqs because it's used in a variety of situations
  - dlqs/destinations
  - event mappings, which require "lookbacks"
"""

DefaultPermissions={"events", "logs", "sqs"}

PatternPermissions=[("\\-table", "dynamodb"),
                    ("\\-bucket", "s3")]

@resource            
def init_function(action):
    resourcename=H("%s-function" % action["name"])
    rolename=H("%s-role" % action["name"])
    memory=H("memory-size-%s" % action["size"])
    timeout=H("timeout-%s" % action["timeout"])
    code={"S3Bucket": {"Ref": H("artifacts-bucket")},
          "S3Key": {"Ref": H("artifacts-key")}}
    handler={"Fn::Sub": "%s/index.handler" % action["name"].replace("-", "/")}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memory},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": handler,
           "Runtime": runtime}
    if "packages" in action:
        props["Layers"]=[{"Ref": H("layer-%s" % pkgname)}
                         for pkgname in action["packages"]]
    if "env" in action:
        variables={U(k): {"Ref": H(k)}
                   for k in action["env"]["variables"]}
        props["Environment"]={"Variables": variables}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

"""
- custom permissions layer provided so you can access polly, translate etc
"""

@resource
def init_role(action, **kwargs):
    def init_permissions(action,
                         defaultpermissions=DefaultPermissions,
                         patternpermissions=PatternPermissions):
        permissions=set(defaultpermissions)
        if "env" in action:
            for var in action["env"]["variables"]:
                for pat, permission in patternpermissions:
                    if re.search(pat, var):
                        permissions.add(permission)
        if "permissions" in action:
            permissions.update(set(action["permissions"]))
        return permissions        
    resourcename=H("%s-role" % action["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    permissions=init_permissions(action)
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : "%s:*" % permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(list(permissions))]}
    policyname={"Fn::Sub": "%s-role-policy-${AWS::StackName}" % action["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_event_config(action):
    resourcename=H("%s-event-config" % action["name"])
    retries=action["retries"] if "retries" in action else 0
    funcname=H("%s-function" % action["name"])
    destarn={"Fn::GetAtt": [H("%s-queue" % action["errors"]), "Arn"]}
    destconfig={"OnFailure": {"Destination": destarn}}
    props={"MaximumRetryAttempts": retries,
           "FunctionName": {"Ref": funcname},
           "Qualifier": "$LATEST",
           "DestinationConfig": destconfig}
    return (resourcename,
            "AWS::Lambda::EventInvokeConfig",
            props)

def init_component(action):
    resources=[]
    fns=[init_function,
         init_role]
    if "errors" in action:
        fns.append(init_event_config)
    for fn in fns:
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
    template["Resources"].update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.template import Template
        template=Template("actions")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
