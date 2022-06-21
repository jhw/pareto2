"""
- quite a lot of the CORS header stuff seems to require single quotes
- these render badly with pyyaml - if you look in the tmp/cloudformation stuff you will see that single quotes inside double quotes are rendered as triple single quotes
- however remember that deploy_stack.py deploys JSON templates rather than YAML; YAML are simply dumped to tmp for convenience and debugging
- reasonable confidence that local JSON parser will handle these single quotes well, and that whatever parses the JSON on the AWS side will do also
- much less confidence about this on the YAML side; but if you ever do need to try and ensure compliance between local and remote YAML parsers, try ruamel.yaml in place of pyyaml
"""

from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

import json, yaml

MethodArn="arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

PermissionSrcArn="arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${%s}/${%s}/%s/%s"

EndpointUrl="https://${%s}.execute-api.${AWS::Region}.${AWS::URLSuffix}/${%s}"

CorsMethodHeader="method.response.header.Access-Control-Allow-%s"

CorsGatewayHeader="gatewayresponse.header.Access-Control-Allow-%s"

CorsHeaders=yaml.safe_load("""
- Content-Type
- X-Amz-Date
- Authorization
- X-Api-Key
- X-Amz-Security-Token
""")

@resource
def init_rest_api(api):
    resourcename=H("%s-rest-api" % api["name"])
    name={"Fn::Sub": "%s-rest-api-${AWS::StackName}" % api["name"]}
    props={"Name": name}
    return (resourcename,            
            "AWS::ApiGateway::RestApi",
            props)

"""
- if you fail to depend on any methods then you get the following 
-  Resource handler returned message: "The REST API doesn't contain any methods (Service: ApiGateway, Status Code: 400, Request ID: 7e343643-cdff-4ca4-9c2f-f94b1b61be5e, Extended Request ID: null)" (RequestToken: ea5517dd-42b4-7e4a-d443-eb3511f34ff5, HandlerErrorCode: InvalidRequest)
"""

@resource
def init_deployment(api, actions):
    resourcename=H("%s-deployment" % api["name"])
    props={"RestApiId": {"Ref": H("%s-rest-api" % api["name"])}}
    depends=[]
    for action in actions:
        if "endpoint" in action:
            depends+=[H("%s-method" % action["name"]),
                      H("%s-cors-method" % action["name"])]
    return (resourcename,            
            "AWS::ApiGateway::Deployment",
            props,
            depends)

@resource
def init_stage(api):
    resourcename=H("%s-stage" % api["name"])
    props={"StageName": api["stage"]["name"],
           "DeploymentId": {"Ref": H("%s-deployment" % api["name"])},
           "RestApiId": {"Ref": H("%s-rest-api" % api["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Stage",
            props)

@resource
def init_authorizer(api, userpool):
    resourcename=H("%s-authorizer" % api["name"])
    name={"Fn::Sub": "%s-authorizer-${AWS::StackName}" % api["name"]}
    providerarn={"Fn::GetAtt": [H("%s-userpool" % userpool["name"]), "Arn"]}
    props={"IdentitySource": "method.request.header.Authorization",
           "Name": name,
           "ProviderARNs": [providerarn],
           "RestApiId": {"Ref": H("%s-rest-api" % api["name"])},
           "Type": "COGNITO_USER_POOLS"}
    return (resourcename,
            "AWS::ApiGateway::Authorizer",
            props)

"""
- https://serverless-stack.com/chapters/handle-api-gateway-cors-errors.html
- otherwise a server error can manifest itself as a CORS error
"""

@resource
def init_default_response(api, code):        
    params={CorsGatewayHeader % k.capitalize(): "'%s'" % v # NB quotes
            for k, v in [("headers", "*"),
                         ("origin", "*")]}
    resourcename=H("%s-cors-default-%s" % (api["name"], code))
    props={"RestApiId": {"Ref": H("%s-rest-api" % api["name"])},
           "ResponseType": "DEFAULT_%s" % code,
           "ResponseParameters": params}
    return (resourcename,
            "AWS::ApiGateway::GatewayResponse",
            props)

@resource
def init_resource(api, action):
    resourcename=H("%s-resource" % action["name"])
    parentid={"Fn::GetAtt": [H("%s-rest-api" % api["name"]),
                             "RootResourceId"]}
    props={"ParentId": parentid,
           "PathPart": action["endpoint"]["path"],
           "RestApiId": {"Ref": H("%s-rest-api" % api["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Resource",
            props)

@resource
def init_method(api, action):
    resourcename=H("%s-method" % action["name"])
    uri={"Fn::Sub": [MethodArn, {"arn": {"Fn::GetAtt": [H("%s-function" % action["name"]), "Arn"]}}]}
    integration={"IntegrationHttpMethod": "POST",
                 "Type": "AWS_PROXY",
                 "Uri": uri}
    props={"HttpMethod": action["endpoint"]["method"],
           "Integration": integration,
           "ResourceId": {"Ref": H("%s-resource" % action["name"])},
           "RestApiId": {"Ref": H("%s-rest-api" % api["name"])},
           "AuthorizationType": "COGNITO_USER_POOLS",
           "AuthorizerId": {"Ref": H("%s-authorizer" % api["name"])}}
    if "parameters" in action["endpoint"]:
        props["RequestValidatorId"]={"Ref": H("%s-validator" % action["name"])}
        props["RequestParameters"]={"method.request.querystring.%s" % param: True
                                    for param in action["endpoint"]["parameters"]}
    elif "schema" in action["endpoint"]:
        props["RequestValidatorId"]={"Ref": H("%s-validator" % action["name"])}
        props["RequestModels"]={"application/json": H("%s-model" % action["name"])}
    return (resourcename,
            "AWS::ApiGateway::Method",
            props)

@resource
def init_cors_method(api, action):
    def init_integration_response(action):
        params={CorsMethodHeader % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", ",".join(CorsHeaders)),
                             ("methods", "%s,OPTIONS" % action["endpoint"]["method"]),
                             ("origin", "*")]}
        templates={"application/json": ""}
        return {"StatusCode": 200,
                "ResponseParameters": params,
                "ResponseTemplates": templates}
    def init_integration(action):
        templates={"application/json": json.dumps({"statusCode": 200})}
        response=init_integration_response(action)
        return {"IntegrationResponses": [response],
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "RequestTemplates": templates,
                "Type": "MOCK"}
    def init_response():
        params={CorsMethodHeader % k.capitalize(): False
                for k in ["headers", "methods", "origin"]}
        models={"application/json": "Empty"}
        return {"StatusCode": 200,
                "ResponseModels": models,
                "ResponseParameters": params}
    resourcename=H("%s-cors-method" % action["name"])
    integration=init_integration(action)
    response=init_response()
    props={"AuthorizationType": "NONE",
           "HttpMethod": "OPTIONS",
           "Integration": integration,
           "MethodResponses": [response],
           "ResourceId": {"Ref": H("%s-resource" % action["name"])},
           "RestApiId": {"Ref": H("%s-rest-api" % api["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Method",
            props)

@resource
def init_permission(api, action):
    resourcename=H("%s-permission" % action["name"])
    sourcearn={"Fn::Sub": PermissionSrcArn % (H("%s-rest-api" % api["name"]),
                                              H("%s-stage" % api["name"]),
                                              action["endpoint"]["method"],
                                              action["endpoint"]["path"])}
    props={"Action": "lambda:InvokeFunction",
           "FunctionName": {"Ref": H("%s-function" % action["name"])},
           "Principal": "apigateway.amazonaws.com",
           "SourceArn": sourcearn}
    return (resourcename, 
            "AWS::Lambda::Permission",
            props)

@resource
def init_validator(api, action):
    resourcename=H("%s-validator" % action["name"])
    props={"RestApiId": {"Ref": H("%s-rest-api" % api["name"])}}
    if "parameters" in action["endpoint"]:
        props["ValidateRequestParameters"]=True
    elif "schema" in action["endpoint"]:
        props["ValidateRequestBody"]=True
    return (resourcename,
            "AWS::ApiGateway::RequestValidator",
            props)

"""
- Name is "optional" but is in fact required if Method is to be able to look up model :/
"""

@resource
def init_model(api, action):
    resourcename=H("%s-model" % action["name"])
    props={"RestApiId": {"Ref": H("%s-rest-api" % api["name"])},
           "ContentType": "application/json",
           "Name": resourcename,
           "Schema": action["endpoint"]["schema"]}
    return (resourcename,
            "AWS::ApiGateway::Model",
            props)    

def init_resources(md):
    def init_resources(api, actions, userpool, resources):
        resources.append(init_rest_api(api))
        resources.append(init_deployment(api, actions))
        resources.append(init_stage(api))
        resources.append(init_authorizer(api, userpool))    
        for code in "4XX|5XX".split("|"):
            resources.append(init_default_response(api, code))
        for action in md.actions:
            if not "endpoint" in action:
                continue
            for fn in [init_resource,
                       init_method,
                       init_permission,
                       init_cors_method]:
                resource=fn(api, action)
                resources.append(resource)
            if "parameters" in action["endpoint"]:
                resources.append(init_validator(api, action))
            elif "schema" in action["endpoint"]:
                resources.append(init_validator(api, action))
                resources.append(init_model(api, action))
    resources=[]
    # START TEMP CODE
    """
    - for the minute, all actions and single user pool are bound to api
    - in future these must be specified at api level
    """
    userpool=md.userpools[0]
    for api in md.apis:
        init_resources(api, md.actions, userpool, resources)
    # END TEMP CODE
    return dict(resources)

"""
- RestApi and Stage (echoed from input) are required for apigw redeployment
"""

def init_outputs(md):
    def init_outputs(api, outputs):
        endpoint={"Fn::Sub": EndpointUrl % (H("%s-rest-api" % api["name"]),
                                            H("%s-stage" % api["name"]))}
        restapi={"Ref": H("%s-rest-api" % api["name"])}
        stage={"Ref": H("%s-stage" % api["name"])}    
        outputs.update({H("%s-endpoint" % api["name"]): {"Value": endpoint},
                        H("%s-rest-api" % api["name"]): {"Value": restapi},
                        H("%s-stage" % api["name"]): {"Value": stage}})
    outputs={}
    for api in md.apis:
        init_outputs(api, outputs)
    return outputs

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
        template=Template("api")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)        
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
