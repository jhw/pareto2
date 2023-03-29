from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_userpool(user):
    resourcename=H("%s-user-userpool" % user["name"])
    passwordpolicy={"MinimumLength": 8,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True,
                    "RequireUppercase": True}
    schema=[{"AttributeDataType": "String",
             "Mutable": True,
             "Name": "email",
             "Required": True,
             "StringAttributeConstraints": {"MinLength": "1"}}]
    props={"AutoVerifiedAttributes": ["email"],
           "Policies": {"PasswordPolicy": passwordpolicy},
           "Schema": schema,
           "UsernameAttributes": ["email"]}
    return (resourcename, 
            "AWS::Cognito::UserPool",
            props)

@resource
def init_userpool_admin_client(user):
    resourcename=H("%s-user-userpool-admin-client" % user["name"])
    props={"UserPoolId": {"Ref": H("%s-user-userpool" % user["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_userpool_web_client(user):
    resourcename=H("%s-user-userpool-web-client" % user["name"])
    props={"UserPoolId": {"Ref": H("%s-user-userpool" % user["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_USER_SRP_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_identitypool(user):
    resourcename=H("%s-user-identitypool" % user["name"])
    props={}
    return (resourcename,
            "AWS::Cognito::IdentityPool",
            props)

"""
@resource
def init_function_role(action, basepermissions=BasePermissions):
    def init_permissions(action, basepermissions):
        permissions=set(basepermissions)
        if "permissions" in action:
            permissions.update(set(action["permissions"]))
        return sorted(list(permissions))
    class Group(list):
        def __init__(self, key, item=[]):
            list.__init__(item)
            self.key=key
        def render(self):
            return ["%s:*" % self.key] if "*" in self else ["%s:%s" % (self.key, value) for value in self]
    def group_permissions(permissions):
        groups={}
        for permission in permissions:
            prefix, suffix = permission.split(":")
            groups.setdefault(prefix, Group(prefix))
            groups[prefix].append(suffix)
        return [group.render()
                for group in list(groups.values())]
    resourcename=H("%s-function-role" % action["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    permissions=init_permissions(action, basepermissions)
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : group,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for group in group_permissions(permissions)]}
    policyname={"Fn::Sub": "%s-function-role-policy-${AWS::StackName}" % action["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)
"""

@resource
def init_unauthorized_role(user):
    resourcename=H("%s-user-unauthorized-role" % user["name"])
    props={}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_authorized_role(user):
    resourcename=H("%s-user-authorized-role" % user["name"])
    props={}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_mapping(user):
    resourcename=H("%s-user-identitypool-mapping" % user["name"])
    props={}
    return (resourcename,
            "AWS::Cognito::IdentityPoolRoleAttachment",
            props)

def render_resources(user):
    resources=[]
    for fn in [init_userpool,
               init_userpool_admin_client,
               init_userpool_web_client,
               init_identitypool,
               init_unauthorized_role,
               init_authorized_role,
               init_identitypool_mapping]:
        resource=fn(user)
        resources.append(resource)
    return dict(resources)

def render_outputs(user):
    outputs={}
    for suffix in ["userpool",
                   "userpool-admin-client",
                   "userpool-web-client",
                   "identitypool"]:
        attr=H("%s-user-%s" % (user["name"], suffix))
        outputs[attr]={"Value": {"Ref": attr}}
    return outputs
            
if __name__=="__main__":
    pass
