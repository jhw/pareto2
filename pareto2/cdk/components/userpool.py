from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

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
    resourcename=H("%s-admin-client" % userpool["name"])
    props={"UserPoolId": {"Ref": H("%s-userpool" % userpool["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_web_client(userpool):
    resourcename=H("%s-web-client" % userpool["name"])
    props={"UserPoolId": {"Ref": H("%s-userpool" % userpool["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_USER_SRP_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

def init_resources(md):
    resources=[]
    userpool=md.userpool
    for fn in [init_userpool,
               init_admin_client,
               init_web_client]:
        resource=fn(userpool)
        resources.append(resource)
    return dict(resources)

def init_outputs(md):
    userpool=md.userpool
    userpool_={"Ref": H("%s-userpool" % userpool["name"])}
    adminclient={"Ref": H("%s-admin-client" % userpool["name"])}
    webclient={"Ref": H("%s-web-client" % userpool["name"])}
    return {H("%s-userpool" % userpool["name"]): {"Value": userpool_},
            H("%s-admin-client" % userpool["name"]): {"Value": adminclient},
            H("%s-web-client" % userpool["name"]): {"Value": webclient}}
            

def update_template(template, md):
    template["Resources"].update(init_resources(md))
    template["Outputs"].update(init_outputs(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.template import Template
        template=Template("userpool")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)        
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
