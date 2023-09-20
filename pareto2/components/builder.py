from pareto2.components import hungarorise as H
from pareto2.components import resource

import yaml

Permissions=["events", "logs", "codebuild", "s3"]

BuildType="LINUX_CONTAINER"
BuildComputeType="BUILD_GENERAL1_SMALL"
BuildImage="aws/codebuild/standard:4.0"

BuildSpec="""
artifacts:
  base-directory: build
  files:
  - '**/*'
  name: $S3_KEY
phases:
  install:
    commands:
    - pip install --upgrade pip
    - mkdir -p build/python
    - pip install --upgrade --target build/python $PIP_TARGET
    runtime-versions:
      python: $PYTHON_RUNTIME
version: '0.2'
"""

"""
- `COMPLETED` does not seem to be an official `completed-phase`; at least you don't seem to get a notification for it; it seems that it appears as a final entry appended to `phases` in the eventbridge FINALIZING message; it does not appear to have an associaed `completed-phase-status`
- not clear if FINALIZING is always generated ?
"""

RulePattern=yaml.safe_load("""
source:
  - "aws.codebuild"
detail-type:
  - "CodeBuild Build Phase Change"
detail:
  completed-phase:
    - SUBMITTED
    - PROVISIONING
    - DOWNLOAD_SOURCE
    - INSTALL
    - PRE_BUILD
    - BUILD
    - POST_BUILD
    - UPLOAD_ARTIFACTS
    - FINALIZING
  completed-phase-status:
    - TIMED_OUT
    - STOPPED
    - FAILED
    - SUCCEEDED
    - FAULT
    - CLIENT_ERROR
""")

@resource
def init_project(builder,
                 buildtype=BuildType,
                 buildcomputetype=BuildComputeType,
                 buildimage=BuildImage,
                 buildspec=BuildSpec,
                 buildprefix="build",
                 logsprefix="logs"):
    resourcename=H("%s-builder-project" % builder["name"])
    env={"ComputeType": buildcomputetype,
         "Image": buildimage,
         "Type": buildtype}
    name={"Fn::Sub": "%s-builder-project-${AWS::StackName}-${AWS::Region}" % builder["name"]}
    source={"Type": "NO_SOURCE",
            "BuildSpec": buildspec}
    rolename=H("%s-builder-service-role" % builder["name"])
    bucketname=H("%s-bucket" % builder["bucket"])
    artifacts={"Type": "S3",
               "Location": {"Ref": bucketname},
               "Packaging": "ZIP",
               "OverrideArtifactName": True,
               "Path": buildprefix}
    s3logspath={"Fn::Sub": "${%s}/%s" % (bucketname,
                                         logsprefix)}
    logsconfig={"S3Logs": {"Status": "ENABLED",
                           "Location": s3logspath}}
    props={"Environment": env,
           "Name": name,
           "Source": source,
           "ServiceRole": {"Fn::GetAtt": [rolename, "Arn"]},
           "Artifacts": artifacts,
           "LogsConfig": logsconfig}
    return (resourcename, 
            "AWS::CodeBuild::Project",
            props)

@resource
def init_service_role(builder, permissions=Permissions):
    resourcename=H("%s-builder-service-role" % builder["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "codebuild.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : "%s:*" % permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(permissions)]}
    policyname={"Fn::Sub": "%s-builder-role-policy-${AWS::StackName}" % builder["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_rule(builder, pattern=RulePattern):
    resourcename=H("%s-builder-rule" % builder["name"])
    pattern["detail"]["project-name"]=[{"Ref": H("%s-builder-project" % builder["name"])}] # *** NB project-name part of detail! ***
    targetid={"Fn::Sub": "%s-builder-rule-${AWS::StackName}" % builder["name"]}
    targetarn={"Fn::GetAtt": [H("%s-function" % builder["action"]), "Arn"]}
    target={"Id": targetid,
            "Arn": targetarn}
    props={"EventPattern": pattern,
           "Targets": [target],
           "State": "ENABLED"}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_rule_permission(builder):
    resourcename=H("%s-builder-rule-permission" % builder["name"])
    sourcearn={"Fn::GetAtt": [H("%s-builder-rule" % builder["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % builder["action"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def render_resources(builder):
    resources=[]
    for fn in [init_project,
               init_service_role,
               init_rule,
               init_rule_permission]:
        resource=fn(builder)
        resources.append(resource)
    return dict(resources)

def render_outputs(builder):
    outputs={}
    project={"Ref": H("%s-builder-project" % builder["name"])}
    outputs[H("%s-builder-project" % builder["name"])]={"Value": project}
    return outputs

if __name__=="__main__":
    pass
