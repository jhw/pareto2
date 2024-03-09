from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Role(Resource):

    def __init__(self, namespace, permissions=[], service="lambda.amazonaws.com"):
        self.namespace = namespace
        self.permissions = permissions
        self.service = service

    @property
    def aws_properties(self):
        policy_name = H(f"{self.namespace}-policy-${{AWS::StackName}}")
        policies = [{"PolicyDocument": self.policy_document,
                     "PolicyName": policy_name}]
        return {
            "AssumeRolePolicyDocument": self.assume_role_policy_document,
            "Policies": policies
        }

    @property
    def policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": [{"Action": self.permissions,
                               "Effect": "Allow",
                               "Resource": "*"}]}

    @property
    def assume_role_policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": [{"Effect": "Allow",
                               "Principal": {"Service": self.service},
                               "Action": "sts:AssumeRole"}]}

