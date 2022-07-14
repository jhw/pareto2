from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

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

def init_resources(md):
    resources=[]
    for userpool in md.userpools:
        for fn in [init_userpool,
                   init_admin_client,
                   init_web_client]:
            resource=fn(userpool)
            resources.append(resource)
    return dict(resources)

def init_outputs(md):
    def init_outputs(userpool, outputs):
        userpool_={"Ref": H("%s-userpool" % userpool["name"])}
        adminclient={"Ref": H("%s-userpool-admin-client" % userpool["name"])}
        webclient={"Ref": H("%s-userpool-web-client" % userpool["name"])}
        outputs.update({H("%s-userpool" % userpool["name"]): {"Value": userpool_},
                        H("%s-userpool-admin-client" % userpool["name"]): {"Value": adminclient},
                        H("%s-userpool-web-client" % userpool["name"]): {"Value": webclient}})
    outputs={}
    for userpool in md.userpools:
        init_outputs(userpool, outputs)
    return outputs
            
def update_template(template, md):
    template.resources.update(init_resources(md))
    template.outputs.update(init_outputs(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.core.template import Template
        template=Template("userpool")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise(stagename)        
        md.validate().expand()
        update_template(template, md)
        template.dump_json(template.filename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
