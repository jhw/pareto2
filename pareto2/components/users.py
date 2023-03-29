from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_userpool(users):
    resourcename=H("%s-users-userpool" % users["name"])
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
def init_userpool_admin_client(users):
    resourcename=H("%s-users-userpool-admin-client" % users["name"])
    props={"UserPoolId": {"Ref": H("%s-users-userpool" % users["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_userpool_web_client(users):
    resourcename=H("%s-users-userpool-web-client" % users["name"])
    props={"UserPoolId": {"Ref": H("%s-users-userpool" % users["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_USER_SRP_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_identitypool(users):
    resourcename=H("%s-users-identitypool" % users["name"])
    props={}
    return (resourcename,
            "AWS::Cognito::IdentityPool",
            props)

@resource
def init_unauthorized_role(users):
    resourcename=H("%s-users-unauthorized-role" % users["name"])
    props={}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_authorized_role(users):
    resourcename=H("%s-users-authorized-role" % users["name"])
    props={}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_mapping(users):
    resourcename=H("%s-users-identitypool-mapping" % users["name"])
    props={}
    return (resourcename,
            "AWS::Cognito::IdentityPoolRoleAttachment",
            props)

def render_resources(users):
    resources=[]
    for fn in [init_userpool,
               init_userpool_admin_client,
               init_userpool_web_client,
               init_identitypool,
               init_unauthorized_role,
               init_authorized_role,
               init_identitypool_mapping]:
        resource=fn(users)
        resources.append(resource)
    return dict(resources)

def render_outputs(users):
    users_={"Ref": H("%s-users-userpool" % users["name"])}
    adminclient={"Ref": H("%s-users-userpool-admin-client" % users["name"])}
    webclient={"Ref": H("%s-users-userpool-web-client" % users["name"])}
    outputs={}
    outputs[H("%s-users-userpool" % users["name"])]={"Value": users_}
    outputs[H("%s-users-userpool-admin-client" % users["name"])]={"Value": adminclient}
    outputs[H("%s-users-userpool-web-client" % users["name"])]={"Value": webclient}
    return outputs
            
if __name__=="__main__":
    pass
