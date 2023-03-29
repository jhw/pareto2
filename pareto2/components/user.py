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
    user_={"Ref": H("%s-user-userpool" % user["name"])}
    adminclient={"Ref": H("%s-user-userpool-admin-client" % user["name"])}
    webclient={"Ref": H("%s-user-userpool-web-client" % user["name"])}
    outputs={}
    outputs[H("%s-user-userpool" % user["name"])]={"Value": user_}
    outputs[H("%s-user-userpool-admin-client" % user["name"])]={"Value": adminclient}
    outputs[H("%s-user-userpool-web-client" % user["name"])]={"Value": webclient}
    return outputs
            
if __name__=="__main__":
    pass
