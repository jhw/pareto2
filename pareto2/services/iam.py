from pareto2.services import hungarorise as H
from pareto2.services import Resource

SimplePermissionsMatcher = lambda item: isinstance(item, str)

ExtendedPermissionsMatcher = lambda item: (instance(item, tuple) and
                                           len(item)==2 and
                                           isinstance(item[0], list) and
                                           isinstance(item[1], str))

def iterlist(items, matcherfn):
    for item in items:
        if not matcherfn(item):
            return False
    return True

def is_simple_permissons(items, matcherfn=SimplePermissionsMatcher):
    return iterlist(items, matcherfn)

def is_extended_permissions(items, matcherfn=ExtendedPermissionsMatcher):
    return iterlist(items, matcherfn)
            
class Role(Resource):

    def __init__(self,
                 namespace,
                 permissions=[],
                 service="lambda.amazonaws.com",
                 action="sts:AssumeRole"):
        self.namespace = namespace
        self.permissions = permissions
        self.service = service
        self.action = action
        
    @property
    def aws_properties(self):
        policy_name = f"{self.namespace}-role-policy-${{AWS::StackName}}"
        policies = [{"PolicyDocument": self.policy_document,
                     "PolicyName": policy_name}]
        return {
            "AssumeRolePolicyDocument": self.assume_role_policy_document,
            "Policies": policies
        }

    def format_permissions(self, permissions):
        if is_simple_permissions_format(permissions):            
            return [(permissions, "*")]
        elif is_extended_permissions_format(permissions):
            return permissions
        else:
            raise RuntimeError("IAM permissions format not identified")
    
    @property
    def policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": [{"Action": permissions,
                               "Effect": "Allow",
                               "Resource": resource}
                              for permissions, resource in self.format_permissions(self.permissions)]}

    @property
    def assume_role_policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": [{"Effect": "Allow",
                               "Principal": {"Service": self.service},
                               "Action": self.action}]}

