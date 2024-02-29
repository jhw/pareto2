from pareto2.aws.s3 import Bucket as BucketBase
from pareto2.aws.iam import Role as RoleBase

class Bucket(BucketBase):

    def __init__(self, website):
        super().__init__(website["name"], "website")

class Role(RoleBase):

    def __init__(self, website, permissions=None):
        super().__init__(website["name"],
                         permissions or ["s3:GetObject"])
        self.service = "apigateway.amazonaws.com"

    def aws_properties(self):
        props = super().aws_properties
        props["AssumeRolePolicyDocument"] = self._assume_role_policy_document(self.service)
        return props
