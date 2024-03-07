from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Role(Resource):

    def __init__(self, component_name, permissions=None, service=None):
        self.component_name = component_name
        self.permissions = permissions or []
        self.service = service

    @property
    def resource_name(self):
        return H(f"{self.component_name}-role")

    @property
    def aws_resource_type(self):
        return "AWS::IAM::Role"

    @property
    def aws_properties(self):
        policy_name = H(f"{self.resource_name}-policy-${{AWS::StackName}}")
        policy_document = self._policy_document(self.permissions)
        policies = [{"PolicyDocument": policy_document, "PolicyName": policy_name}]
        assume_role_policy_document = self._assume_role_policy_document()
        return {
            "AssumeRolePolicyDocument": assume_role_policy_document,
            "Policies": policies
        }

    def _policy_document(self, permissions):
        # Simulate policy_document function's behavior
        return {"Version": "2012-10-17", "Statement": [{"Action": permissions, "Effect": "Allow", "Resource": "*"}]}

    def _assume_role_policy_document(self, service=None):
        # Simulate assume_role_policy_document function's behavior, optionally for a specific service
        principal_service = service or "sts.amazonaws.com"
        return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": principal_service}, "Action": "sts:AssumeRole"}]}

