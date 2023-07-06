from botocore.exceptions import ClientError

import boto3, json, os, time, yaml

"""
- https://urllib3.readthedocs.io/en/stable/v2-migration-guide.html#importerror-cannot-import-name-default-ciphers-from-urllib3-util-ssl
"""

"""
If you’re deploying to an AWS environment such as Lambda or a host using Amazon Linux 2, you’ll need to explicitly pin to urllib3<2 in your project to ensure urllib3 2.0 isn’t brought into your environment. Otherwise, this may result in unintended side effects with the default boto3 installation.
"""

BuildSpec=yaml.safe_load("""
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
""")

RolePolicyDoc=yaml.safe_load("""
Statement:
  - Action: sts:AssumeRole
    Effect: Allow
    Principal:
      Service: codebuild.amazonaws.com
Version: '2012-10-17'
""")

DockerImage="aws/codebuild/standard:6.0"

def assert_role(fn):
    def role_name(config):
        return "%s-codebuild-layers-role" % config["AppName"]
    def policy_name(rolename):
        return "%s-policy" % rolename
    def create_role(iam,
                    rolename,
                    permissions=["codebuild:*",
                                 "s3:*",
                                 "logs:*"],
                    rolepolicydoc=RolePolicyDoc):
        role=iam.create_role(RoleName=rolename,
                             AssumeRolePolicyDocument=json.dumps(rolepolicydoc))
        policydoc={"Statement": [{"Action": permission,
                                  "Effect": "Allow",
                                  "Resource": "*"}
                                 for permission in permissions],
                   "Version": "2012-10-17"}
        policy=iam.create_policy(PolicyName=policy_name(rolename),
                                 PolicyDocument=json.dumps(policydoc))
        print ("waiting for policy creation ..")
        waiter=iam.get_waiter("policy_exists")
        waiter.wait(PolicyArn=policy["Policy"]["Arn"])
        iam.attach_role_policy(RoleName=rolename,
                               PolicyArn=policy["Policy"]["Arn"])
        return role["Role"]["Arn"]
    def wrapped(cb, iam, config):
        rolename=role_name(config)
        rolearns={role["RoleName"]:role["Arn"]
                  for role in iam.list_roles()["Roles"]}
        if rolename in rolearns:
            print ("role exists")
            rolearn=rolearns[rolename]
        else:
            print ("creating role")
            rolearn=create_role(iam, rolename)
            print ("waiting for role creation ..")
            waiter=iam.get_waiter("role_exists")
            waiter.wait(RoleName=rolename)
        return fn(cb, iam, config, rolearn)
    return wrapped

@assert_role
def init_project(cb, iam, config, rolearn,
                 buildspec=yaml.safe_dump(BuildSpec,
                                          default_flow_style=False), # NB
                 maxtries=20,
                 wait=5):
    projectname="%s-layers" % config["AppName"]
    bucketname=config["ArtifactsBucket"]
    for i in range(maxtries):
        try:
            print ("trying to create project [%i/%i]" % (i+1, maxtries))
            project=cb.create_project(name=projectname,
                                      source={"type": "NO_SOURCE",
                                              "buildspec": buildspec},
                                      artifacts={"type": "S3",
                                                 "location": bucketname,
                                                 "path": "",
                                                 "overrideArtifactName": True,
                                                 "packaging": "ZIP"},
                                      environment={"type": "LINUX_CONTAINER",
                                                   "image": DockerImage,
                                                   "computeType": "BUILD_GENERAL1_SMALL"},
                                      serviceRole=rolearn)
            print ("project created :)")
            return project
        except ClientError as error:
            print ("Error: %s" % error)
            time.sleep(wait)
    raise RuntimeError("couldn't create codebuild project")
                          
if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        bucketname=os.environ["ARTIFACTS_BUCKET"]
        if bucketname in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        config={"AppName": appname,
                "ArtifactsBucket": bucketname}
        cb=boto3.client("codebuild")
        iam=boto3.client("iam")
        init_project(cb, iam, config)
    except ClientError as error:
        print ("Error: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))

