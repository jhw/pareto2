from pareto2.services import hungarorise as H
from pareto2.services import Resource

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

def is_list_of_strings(items, matcherfn = lambda x: isinstance(x, str)):
    return list_matcher(items, matcherfn)

def is_list_of_dicts(items, matcherfn =  lambda x: isinstance(x, dict)):
    return list_matcher(items, matcherfn)

def listify(values):
    return [values] if not isinstance(values, list) else values

class Role(Resource):

    def __init__(self,
                 namespace,
                 action = "sts:AssumeRole",
                 condition = None,
                 principal = "lambda.amazonaws.com"):
        self.namespace = namespace
        self.action = action
        self.condition = condition
        self.principal = principal

    @property
    def aws_properties(self):
        return {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [self.statement]
            }
        }
    
    @property
    def statement(self):
        statement= {
            "Effect": "Allow",
            "Principal": {"Service": self.principal} if isinstance(self.principal, str) else self.principal,
            "Action": listify(self.action)
        }
        if self.condition:
            statement["Condition"] = self.condition
        return statement

"""
It's good to have some default permissions specified as Cloudformation will fail with empty list
"""
    
class Policy(Resource):

    def __init__(self,
                 namespace,
                 permissions = ["logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"]):
        self.namespace = namespace
        self.permissions = permissions
        
    @property
    def aws_properties(self):
        return {
            "Roles": [
                {"Ref": H(f"{self.namespace}-role")},
            ],
            "PolicyName": {"Fn::Sub": f"{self.namespace}-policy-${{AWS::StackName}}"},
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": self.init_statement(self.permissions)
            }
        }

    def init_statement(self, permissions):
        if is_list_of_strings(permissions):            
            return self.simple_permissions(permissions)
        elif is_list_of_dicts(permissions):
            return self.expanded_permissions(permissions)
        else:
            raise RuntimeError("IAM permissions format not recognised")
    
    def simple_permissions(self, permissions):
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

    def expanded_permissions(self, items):
        return [{"Action": listify(item["action"]),
                 "Effect": "Allow",
                 "Resource": item["resource"] if "resource" in item else "*"}
                for item in items]
    
