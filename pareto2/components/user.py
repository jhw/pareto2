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

"""
- an identity pool shouldn't really be required; however
  - https://github.com/aws-amplify/amplify-flutter/issues/431
  - https://github.com/aws-amplify/amplify-flutter/issues/2779
"""

@resource
def init_identitypool(user):
    resourcename=H("%s-user-identitypool" % user["name"])
    clientid={"Ref": H("%s-user-userpool-web-client" % user["name"])}
    providername={"Fn::GetAtt": [H("%s-user-userpool" % user["name"]),
                                 "ProviderName"]}
    provider={"ClientId": clientid,
              "ProviderName": providername}
    props={"AllowUnauthenticatedIdentities": True,
           "CognitoIdentityProviders": [provider]}
    return (resourcename,
            "AWS::Cognito::IdentityPool",
            props)

def init_assume_role_policy_doc(user, typestr):
    condition={"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H("%s-user-identitypool" % user["name"])}},
               "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
    statement={"Effect": "Allow",
               "Principal": {"Federated": "cognito-identity.amazonaws.com"},
               "Action": ["sts:AssumeRoleWithWebIdentity"],
               "Condition": condition}
    return {"Version": "2012-10-17",
            "Statement": [statement]}

def init_policy_document(groups):
    statement=[{"Effect": "Allow",
                "Action": actions,
                "Resource": "*"}
               for actions in groups]
    return {"Version": "2012-10-17",
            "Statement": [statement]}

@resource
def init_unauthorized_role(user,
                           groups=[["mobileanalytics:PutEvents",
                                    "cognito-sync:*"]]):
    resourcename=H("%s-user-unauthorized-role" % user["name"])
    assumerolepolicydoc=init_assume_role_policy_doc(user, "unauthenticated")
    policyname=H("%s-user-unauthorized-role-policy" % user["name"])
    policydoc=init_policy_document(groups)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_authorized_role(user,
                         groups=[["mobileanalytics:PutEvents",
                                  "cognito-sync:*",
                                  "cognito-identity:*"],
                                 ["lambda:InvokeFunction"]]):
    resourcename=H("%s-user-authorized-role" % user["name"])
    assumerolepolicydoc=init_assume_role_policy_doc(user, "authenticated")
    policyname=H("%s-user-authorized-role-policy" % user["name"])
    policydoc=init_policy_document(groups)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_mapping(user):
    resourcename=H("%s-user-identitypool-mapping" % user["name"])
    identitypoolid={"Ref": H("%s-user-identitypool" % user["name"])}
    authrole={"Fn::GetAtt": [H("%s-user-authorized-role" % user["name"]),
                             "Arn"]}
    unauthrole={"Fn::GetAtt": [H("%s-user-unauthorized-role" % user["name"]),
                               "Arn"]}
    roles={"authenticated": authrole,
           "unauthenticated": unauthrole}
    props={"Roles": roles,
           "IdentityPoolId": identitypoolid}
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
