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

def render_resources(users):
    resources=[]
    for fn in [init_userpool,
               init_userpool_admin_client,
               init_userpool_web_client]:
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
