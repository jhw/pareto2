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

"""
Technically speaking "lambda.amazonaws.com" is a service whilst {"Service": "lambda.amazonaws.com"} is a principal; but it's convenient to call them both principal as sometimes principal needs to be overwritten with an expression in which the key is not "Service" (eg Cognito -> "Federated")
"""

class Role(Resource):

    def __init__(self,
                 namespace,
                 action = "sts:AssumeRole",
                 condition = None,
                 principal = "lambda.amazonaws.com",
                 version = "2012-10-17"):
        super().__init__(namespace)
        self.action = action
        self.condition = condition
        self.principal = principal
        self.version = version

    @property
    def aws_properties(self):
        return {
            "AssumeRolePolicyDocument": {
                "Version": self.version,
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
                                "logs:PutLogEvents"],
                 version = "2012-10-17"):
        super().__init__(namespace)
        self.permissions = permissions
        self.version = version

    @property
    def statement(self):
        if is_list_of_strings(self.permissions):            
            return SimpleStatement(self.permissions)
        elif is_list_of_dicts(self.permissions):
            return ExtendedStatement(self.permissions)
        else:
            raise RuntimeError("IAM permissions format not recognised")
        
    @property
    def aws_properties(self):
        return {
            "Roles": [
                {"Ref": H(f"{self.namespace}-role")},
            ],
            "PolicyName": {"Fn::Sub": f"{self.namespace}-policy-${{AWS::StackName}}"},
            "PolicyDocument": {
                "Version": self.version,
                "Statement": self.statement
            }
        }

class Statement(list):

    pass

class SimpleStatement(Statement):

    def __init__(self, permissions):
        def group_permissions(permissions):
            groups = {}
            for permission in permissions:
                service = permission.split(":")[0]
                groups.setdefault(service, [])
                groups[service].append(permission)
            return list(groups.values())
        super().__init__([PermissionsGroup({"Action": group,
                                            "Effect": "Allow",
                                            "Resource": "*"})
                          for group in group_permissions(permissions)])

class ExtendedStatement(Statement):

    def __init__(self, items):
        super().__init__([PermissionsGroup({"Action": listify(item["action"]),
                                            "Effect": "Allow",
                                            "Resource": item["resource"] if "resource" in item else "*"})
                          for item in items])
    
class PermissionsGroup(dict):
    
    pass
