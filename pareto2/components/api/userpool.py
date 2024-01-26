from pareto2.components import hungarorise as H
from pareto2.components import resource

from pareto2.components.common.iam import policy_document

@resource
def init_userpool(user):
    resourcename=H("%s-userpool" % api["name"])
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
    resourcename=H("%s-userpool-admin-client" % api["name"])
    props={"UserPoolId": {"Ref": H("%s-userpool" % api["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_userpool_web_client(user):
    resourcename=H("%s-userpool-web-client" % api["name"])
    props={"UserPoolId": {"Ref": H("%s-userpool" % api["name"])},
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
    resourcename=H("%s-identitypool" % api["name"])
    clientid={"Ref": H("%s-userpool-web-client" % api["name"])}
    providername={"Fn::GetAtt": [H("%s-userpool" % api["name"]),
                                 "ProviderName"]}
    provider={"ClientId": clientid,
              "ProviderName": providername}
    props={"AllowUnauthenticatedIdentities": True,
           "CognitoIdentityProviders": [provider]}
    return (resourcename,
            "AWS::Cognito::IdentityPool",
            props)

def role_policy_document(user, typestr):
    condition={"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H("%s-identitypool" % api["name"])}},
               "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
    statement=[{"Effect": "Allow",
                "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                "Action": ["sts:AssumeRoleWithWebIdentity"],
                "Condition": condition}]
    return {"Version": "2012-10-17",
            "Statement": statement}

@resource
def init_identitypool_unauthorized_role(user,
                                        permissions=["mobileanalytics:PutEvents",
                                                     "cognito-sync:*"]):
    resourcename=H("%s-identitypool-unauthorized-role" % api["name"])
    assumerolepolicydoc=role_policy_document(user, "unauthenticated")
    policyname=H("%s-identitypool-unauthorized-role-policy" % api["name"])
    policydoc=policy_document(permissions)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_authorized_role(user,
                                      permissions=["mobileanalytics:PutEvents",
                                                   "cognito-sync:*",
                                                   "cognito-identity:*",
                                                   "lambda:InvokeFunction"]):
    resourcename=H("%s-identitypool-authorized-role" % api["name"])
    assumerolepolicydoc=role_policy_document(user, "authenticated")
    policyname=H("%s-identitypool-authorized-role-policy" % api["name"])
    policydoc=policy_document(permissions)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_mapping(user):
    resourcename=H("%s-identitypool-mapping" % api["name"])
    identitypoolid={"Ref": H("%s-identitypool" % api["name"])}
    authrole={"Fn::GetAtt": [H("%s-identitypool-authorized-role" % api["name"]),
                             "Arn"]}
    unauthrole={"Fn::GetAtt": [H("%s-identitypool-unauthorized-role" % api["name"]),
                               "Arn"]}
    roles={"authenticated": authrole,
           "unauthenticated": unauthrole}
    props={"Roles": roles,
           "IdentityPoolId": identitypoolid}
    return (resourcename,
            "AWS::Cognito::IdentityPoolRoleAttachment",
            props)

"""
def render_resources(user):
    resources=[]
    for fn in [init_userpool,
               init_userpool_admin_client,
               init_userpool_web_client,
               init_identitypool,
               init_identitypool_unauthorized_role,
               init_identitypool_authorized_role,
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
        attr=H("%s-%s" % (api["name"], suffix))
        outputs[attr]={"Value": {"Ref": attr}}
    return outputs
"""
            
if __name__=="__main__":
    pass
