from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Project(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def visible(self):
        return True

class S3Project(Project):

    def __init__(self,
                 namespace,
                 build_spec,
                 artifacts_name = "artifacts.zip",
                 artifacts_path = "build"):
        super().__init__(namespace)
        self.build_spec = build_spec
        self.artifacts_name = artifacts_name
        self.artifacts_path = artifacts_path

    @property
    def environment(self):
        return {
            "Type" :"LINUX_CONTAINER",
            "ComputeType": "BUILD_GENERAL1_SMALL",
            "Image": "aws/codebuild/standard:6.0"
        }

    @property
    def source(self):               
        return {
            "Type": "NO_SOURCE",
            "BuildSpec": self.build_spec
        }

    """
    - magic combination of Path, NamespaceType and Name should result in artifacts pushing to build/#{build-id}/artifacts.zip where build-id only contains the uuid component (and not the project name component)
    - remember build-id is `#{project-name}:#{uuid}`; and colons are not valid s3 key characters
    - if you don't specify NAME then project-name will be used as Name, weirdly
    """
    
    @property
    def artifacts(self):
        return {
            "Type": "S3",
            "Location": {"Ref": H(f"{self.namespace}-bucket")},
            "Packaging": "ZIP",
            "Name": self.artifacts_name,
            "NamespaceType": "BUILD_ID",
            "Path": self.artifacts_path
        }

    @property
    def logs_config(self):
        bucket_ref = H(f"{self.namespace}-bucket")
        return {
            "S3Logs": {
                "Location": {"Fn::Sub": f"${{{bucket_ref}}}/logs"},
                "Status": "ENABLED"
            }
        }
    
    @property
    def aws_properties(self):
         return {
             "ServiceRole": {"Fn::GetAtt": [H(f"{self.namespace}-role"), "Arn"]},
             "Environment": self.environment,
             "Source": self.source,
             "Artifacts": self.artifacts,
             "LogsConfig": self.logs_config
         }

