from pareto2.components import hungarorise as H
from pareto2.components import resource

import yaml

Permissions=["events", "logs", "codebuild", "s3"]

BuildType="LINUX_CONTAINER"
BuildComputeType="BUILD_GENERAL1_SMALL"
BuildImage="aws/codebuild/standard:6.0"

"""
If you’re deploying to an AWS environment such as Lambda or a host using Amazon Linux 2, you’ll need to explicitly pin to urllib3<2 in your project to ensure urllib3 2.0 isn’t brought into your environment. Otherwise, this may result in unintended side effects with the default boto3 installation.
"""

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
    - pip install --upgrade --target build/python $PIP_TARGET 'urllib3<2'
    runtime-versions:
      python: $PYTHON_RUNTIME
version: '0.2'
"""

@resource
def init_project(builder,
                 buildtype=BuildType,
                 buildcomputetype=BuildComputeType,
                 buildimage=BuildImage,
                 buildspec=BuildSpec,
                 buildprefix="build",
                 logsprefix="logs"):
    resourcename=H("%s-builder" % builder["name"])
    env={"ComputeType": buildcomputetype,
         "Image": buildimage,
         "Type": buildtype}
    name={"Fn::Sub": "%s-builder-${AWS::StackName}-${AWS::Region}" % builder["name"]}
    source={"Type": "NO_SOURCE",
            "BuildSpec": buildspec}
    rolename=H("%s-builder-service-role" % builder["name"])
    bucketname=H("%s-bucket" % builder["name"]) # NB core app bucket not dedicated
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

def render_resources(builder):
    resources=[]
    for fn in [init_project,
               init_service_role]:
        resource=fn(builder)
        resources.append(resource)
    return dict(resources)

def render_outputs(builder):
    outputs={}
    project={"Ref": H("%s-builder" % builder["name"])}
    outputs[H("%s-builder" % builder["name"])]={"Value": project}
    return outputs

if __name__=="__main__":
    pass
