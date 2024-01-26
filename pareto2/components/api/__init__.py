from pareto2.components import hungarorise as H
from pareto2.components import resource

from pareto2.components.api.cors import init_cors_deployment, init_cors_default_response, init_cors_method
from pareto2.components.api.domain import init_domain, init_domain_path_mapping, init_domain_record_set
from pareto2.components.api.methods import init_method, init_open_method, init_cognito_method
from pareto2.components.api.validation import init_validator, init_model

import json

PermissionSrcArn="arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${%s}/${%s}/%s/%s"

EndpointUrl="https://${%s}.execute-api.${AWS::Region}.${AWS::URLSuffix}/${%s}"

@resource
def init_rest_api(api):
    resourcename=H("%s-api-rest-api" % api["name"])
    name={"Fn::Sub": "%s-api-rest-api-${AWS::StackName}" % api["name"]}
    props={"Name": name}
    return (resourcename,            
            "AWS::ApiGateway::RestApi",
            props)

@resource
def init_stage(api):
    resourcename=H("%s-api-stage" % api["name"])
    props={"StageName": api["stage"]["name"],
           "DeploymentId": {"Ref": H("%s-api-deployment" % api["name"])},
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Stage",
            props)

@resource
def init_cognito_authorizer(api):
    resourcename=H("%s-api-authorizer" % api["name"])
    name={"Fn::Sub": "%s-api-authorizer-${AWS::StackName}" % api["name"]}
    providerarn={"Fn::GetAtt": [H("%s-userpool" % api["user"]), "Arn"]}
    props={"IdentitySource": "method.request.header.Authorization",
           "Name": name,
           "ProviderARNs": [providerarn],
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "Type": "COGNITO_USER_POOLS"}
    return (resourcename,
            "AWS::ApiGateway::Authorizer",
            props)

@resource
def init_resource(api, endpoint):
    resourcename=H("%s-api-resource" % endpoint["name"])
    parentid={"Fn::GetAtt": [H("%s-api-rest-api" % api["name"]),
                             "RootResourceId"]}
    props={"ParentId": parentid,
           "PathPart": endpoint["path"],
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Resource",
            props)

@resource
def init_permission(api, endpoint):
    resourcename=H("%s-api-permission" % endpoint["name"])
    sourcearn={"Fn::Sub": PermissionSrcArn % (H("%s-api-rest-api" % api["name"]),
                                              H("%s-api-stage" % api["name"]),
                                              endpoint["method"],
                                              endpoint["path"])}
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": {"Ref": H("%s-function" % endpoint["action"])},
           "Principal": "apigateway.amazonaws.com",
           "SourceArn": sourcearn}
    return (resourcename, 
            "AWS::Lambda::Permission",
            props)

"""
- public api includes CORS options to simplify local UI development
"""

def init_open_resources(api, resources):
    for fn in [init_rest_api,
               init_cors_deployment,
               init_stage,
               init_domain,
               init_domain_path_mapping,
               init_domain_record_set]:
        resources.append(fn(api))
    for code in "4XX|5XX".split("|"):
        resources.append(init_cors_default_response(api, code))
    for endpoint in api["endpoints"]:
        for fn in [init_resource,
                   init_open_method,
                   init_permission,
                   init_cors_method]:
            resource=fn(api, endpoint)
            resources.append(resource)
        if "parameters" in endpoint:
            resources.append(init_validator(api, endpoint))
        elif "schema" in endpoint:
            resources.append(init_validator(api, endpoint))
            resources.append(init_model(api, endpoint))

def init_cognito_resources(api, resources):
    for fn in [init_rest_api,
               init_cors_deployment,
               init_stage,
               init_cognito_authorizer,
               init_domain,
               init_domain_path_mapping,
               init_domain_record_set]:
        resources.append(fn(api))
    for code in "4XX|5XX".split("|"):
        resources.append(init_cors_default_response(api, code))
    for endpoint in api["endpoints"]:
        for fn in [init_resource,
                   init_cognito_method,
                   init_permission,
                   init_cors_method]:
            resource=fn(api, endpoint)
            resources.append(resource)
        if "parameters" in endpoint:
            resources.append(init_validator(api, endpoint))
        elif "schema" in endpoint:
            resources.append(init_validator(api, endpoint))
            resources.append(init_model(api, endpoint))

def render_resources(api):
    resources=[]
    if ("auth-type" not in api or
        api["auth-type"]=="open"):
        init_open_resources(api, resources)
    elif api["auth-type"]=="cognito":
        init_cognito_resources(api, resources)
    else:
        raise RuntimeError("%s api type '%s' not recognised" % (api["name"], api["auth-type"]))
    return dict(resources)

"""
- RestApi and Stage (echoed from input) are required for apigw redeployment
"""

def render_outputs(api):
    endpoint={"Fn::Sub": EndpointUrl % (H("%s-api-rest-api" % api["name"]),
                                        H("%s-api-stage" % api["name"]))}
    outputs={}
    for k, v in {"endpoint":endpoint}.items():
        outputs[H("%s-%s" % (api["name"], k))]={"Value": v}
    return outputs

if __name__=="__main__":
    pass
