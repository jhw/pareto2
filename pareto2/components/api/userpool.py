from pareto2.components import hungarorise as H
from pareto2.components import resource

from pareto2.components.common.iam import policy_document

@resource
def init_userpool(api):
    resourcename=H("%s-api-userpool" % api["name"])
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
def init_userpool_admin_client(api):
    resourcename=H("%s-api-userpool-admin-client" % api["name"])
    props={"UserPoolId": {"Ref": H("%s-api-userpool" % api["name"])},
           "PreventUserExistenceErrors": "ENABLED",
           "ExplicitAuthFlows": ["ALLOW_ADMIN_USER_PASSWORD_AUTH",
                                 "ALLOW_REFRESH_TOKEN_AUTH"]}
    return (resourcename, 
            "AWS::Cognito::UserPoolClient",
            props)

@resource
def init_userpool_web_client(api):
    resourcename=H("%s-api-userpool-web-client" % api["name"])
    props={"UserPoolId": {"Ref": H("%s-api-userpool" % api["name"])},
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
def init_identitypool(api):
    resourcename=H("%s-api-identitypool" % api["name"])
    clientid={"Ref": H("%s-api-userpool-web-client" % api["name"])}
    providername={"Fn::GetAtt": [H("%s-api-userpool" % api["name"]),
                                 "ProviderName"]}
    provider={"ClientId": clientid,
              "ProviderName": providername}
    props={"AllowUnauthenticatedIdentities": True,
           "CognitoIdentityProviders": [provider]}
    return (resourcename,
            "AWS::Cognito::IdentityPool",
            props)

def role_policy_document(api, typestr):
    condition={"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H("%s-api-identitypool" % api["name"])}},
               "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
    statement=[{"Effect": "Allow",
                "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                "Action": ["sts:AssumeRoleWithWebIdentity"],
                "Condition": condition}]
    return {"Version": "2012-10-17",
            "Statement": statement}

@resource
def init_identitypool_unauthorized_role(api,
                                        permissions=["mobileanalytics:PutEvents",
                                                     "cognito-sync:*"]):
    resourcename=H("%s-api-identitypool-unauthorized-role" % api["name"])
    assumerolepolicydoc=role_policy_document(api, "unauthenticated")
    policyname=H("%s-api-identitypool-unauthorized-role-policy" % api["name"])
    policydoc=policy_document(permissions)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_authorized_role(api,
                                      permissions=["mobileanalytics:PutEvents",
                                                   "cognito-sync:*",
                                                   "cognito-identity:*",
                                                   "lambda:InvokeFunction"]):
    resourcename=H("%s-api-identitypool-authorized-role" % api["name"])
    assumerolepolicydoc=role_policy_document(api, "authenticated")
    policyname=H("%s-api-identitypool-authorized-role-policy" % api["name"])
    policydoc=policy_document(permissions)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

@resource
def init_identitypool_mapping(api):
    resourcename=H("%s-api-identitypool-mapping" % api["name"])
    identitypoolid={"Ref": H("%s-api-identitypool" % api["name"])}
    authrole={"Fn::GetAtt": [H("%s-api-identitypool-authorized-role" % api["name"]),
                             "Arn"]}
    unauthrole={"Fn::GetAtt": [H("%s-api-identitypool-unauthorized-role" % api["name"]),
                               "Arn"]}
    roles={"authenticated": authrole,
           "unauthenticated": unauthrole}
    props={"Roles": roles,
           "IdentityPoolId": identitypoolid}
    return (resourcename,
            "AWS::Cognito::IdentityPoolRoleAttachment",
            props)

if __name__=="__main__":
    pass
