from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Role(Resource):

    def __init__(self, namespace, permissions=[], service="lambda.amazonaws.com"):
        self.namespace = namespace
        self.permissions = permissions
        self.service = service
        
    @property
    def aws_properties(self):
        policy_name = f"{self.namespace}-role-policy-${{AWS::StackName}}"
        policies = [{"PolicyDocument": self.policy_document,
                     "PolicyName": policy_name}]
        return {
            "AssumeRolePolicyDocument": self.assume_role_policy_document,
            "Policies": policies
        }

    def group_permissions(self, permissions):
        groups={}
        for permission in permissions:
            service=permission.split(":")[0]
            groups.setdefault(service, [])
            groups[service].append(permission)
        return list(groups.values())
    
    @property
    def policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": [{"Action": group,
                               "Effect": "Allow",
                               "Resource": "*"}
                              for group in self.group_permissions(self.permissions)]}

    @property
    def assume_role_policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": [{"Effect": "Allow",
                               "Principal": {"Service": self.service},
                               "Action": "sts:AssumeRole"}]}
