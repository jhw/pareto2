from pareto2.services import hungarorise as H
from pareto2.services import Resource

SimpleMatcher = lambda item: isinstance(item, str)

ExtendedMatcher = lambda item: isinstance(item, dict)

def is_list(fn):
    def wrapped(items, matcherfn):
        if not isinstance(items, list):
            raise RuntimeError("IAM permissions must be a list")
        return fn(items, matcherfn)
    return wrapped

@is_list
def list_matcher(items, matcherfn):
    for item in items:
        if not matcherfn(item):
            return False
    return True

def is_list_of_strings(items, matcherfn = SimpleMatcher):
    return list_matcher(items, matcherfn)

def is_list_of_dicts(items, matcherfn = ExtendedMatcher):
    return list_matcher(items, matcherfn)

def listify(values):
    return [values] if not isinstance(values, list) else values

class Role(Resource):

    def __init__(self,
                 namespace,
                 action = "sts:AssumeRole",
                 condition = None,
                 principal = "lambda.amazonaws.com",
                 permissions = []):
        self.namespace = namespace
        self.action = action
        self.condition = condition
        self.principal = principal
        self.permissions = permissions
        
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
                      "Principal": {"Service": self.principal} if isinstance(self.principal, str) else self.principal,
                      "Action": listify(self.action)}]
        if self.condition:
            statement["Condition"] = self.condition
        return {"Version": "2012-10-17",
                "Statement": statement}
    
    def format_simple_policies(self, permissions):
        def group_permissions(permissions):
            groups = {}
            for permission in permissions:
                service = permission.split(":")[0]
                groups.setdefault(service, [])
                groups[service].append(permission)
            return list(groups.values())
        return [{"Action": group,
                 "Effect": "Allow",
                 "Resource": "*"}
                for group in group_permissions(permissions)]

    def format_extended_policies(self, items):
        return [{"Action": listify(item["action"]),
                 "Effect": "Allow",
                 "Resource": item["resource"] if "resource" in item else "*"}
                for item in items]
    
    def format_policies(self, permissions):
        if is_list_of_strings(permissions):            
            return self.format_simple_policies(permissions)
        elif is_list_of_dicts(permissions):
            return self.format_extended_policies(permissions)
        else:
            raise RuntimeError("IAM permissions format not recognised")

    @property
    def policy_document(self):
        return {"Version": "2012-10-17",
                "Statement": self.format_policies(self.permissions)}


