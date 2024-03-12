from pareto2.services import hungarorise as H
from pareto2.services import Resource

SimpleMatcher = lambda item: isinstance(item, str)

ExtendedMatcher = lambda item: isinstance(item, dict)

def list_match(items, matcherfn):
    for item in items:
        if not matcherfn(item):
            return False
    return True

def is_simple_format(items, matcherfn=SimpleMatcher):
    return list_match(items, matcherfn)

def is_extended_format(items, matcherfn=ExtendedMatcher):
    return list_match(items, matcherfn)
            
class Role(Resource):

    def __init__(self,
                 namespace,
                 permissions=[],
                 principal={"Service": "lambda.amazonaws.com"},
                 action=["sts:AssumeRole"],
                 condition=None):
        self.namespace = namespace
        self.permissions = permissions
        self.principal = principal
        self.action = action
        self.condition = condition
        
    @property
    def aws_properties(self):
        policy_name = f"{self.namespace}-role-policy-${{AWS::StackName}}"
        policies = [{"PolicyDocument": self.policy_document,
                     "PolicyName": policy_name}]
        return {
            "AssumeRolePolicyDocument": self.assume_role_policy_document,
            "Policies": policies
        }

    @property
    def assume_role_policy_document(self):
        statement = [{"Effect": "Allow",
                      "Principal": self.principal,
                      "Action": self.action}]
        if self.condition:
            statement["Condition"] = self.condition
        return {"Version": "2012-10-17",
                "Statement": statement}
    
    def format_simple_policy_statement(self, permissions):
        def group_permissions(permissions):
            groups={}
            for permission in permissions:
                service = permission.split(":")[0]
                groups.setdefault(service, [])
                groups[service].append(permission)
            return list(groups.values())
        return [{"Action": group,
                 "Effect": "Allow",
                 "Resource": "*"}
                for group in group_permissions(permissions)]

    def format_extended_policy_statement(self, items):
        return [{"Action": item["action"],
                 "Effect": "Allow",
                 "Resource": item["resource"] if "resource" in item else "*"}
                for item in items]
    
    def format_policy_statement(self, permissions):
        if is_simple_format(permissions):            
            return self.format_simple_policy_statement(permissions)
        elif is_extended_format(permissions):
            return self.format_extended_policy_statement(permissions)
        else:
            raise RuntimeError("IAM permissions format not identified")

    @property
    def policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": self.format_policy_statement(self.permissions)}


