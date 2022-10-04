from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_userpool(userpool):
    resourcename=H("%s-userpool" % userpool["name"])
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
def init_admin_client(userpool):
    resourcename=H("%s-userpool-admin-client" % userpool["name"])
    props={"UserPoolId": {"Ref": H("%s-userpool" % userpool["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_web_client(userpool):
    resourcename=H("%s-userpool-web-client" % userpool["name"])
    props={"UserPoolId": {"Ref": H("%s-userpool" % userpool["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_USER_SRP_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

def render_resources(userpool):
    resources=[]
    for fn in [init_userpool,
               init_admin_client,
               init_web_client]:
        resource=fn(userpool)
        resources.append(resource)
    return dict(resources)

def render_outputs(userpool):
    userpool_={"Ref": H("%s-userpool" % userpool["name"])}
    adminclient={"Ref": H("%s-userpool-admin-client" % userpool["name"])}
    webclient={"Ref": H("%s-userpool-web-client" % userpool["name"])}
    outputs={}
    outputs[H("%s-userpool" % userpool["name"])]={"Value": userpool_}
    outputs[H("%s-userpool-admin-client" % userpool["name"])]={"Value": adminclient}
    outputs[H("%s-userpool-web-client" % userpool["name"])]={"Value": webclient}
    return outputs
            
if __name__=="__main__":
    try:
        from pareto2.dsl import Config
        config=Config.init_file()
        from pareto2.template import Template
        template=Template("userpools")
        for userpool in config["components"].userpools:
            template.resources.update(render_resources(userpool))
            template.outputs.update(render_outputs(userpool))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
