"""
- quite a lot of the CORS header stuff seems to require single quotes
- these render badly with pyyaml - if you look in the tmp/cloudformation stuff you will see that single quotes inside double quotes are rendered as triple single quotes
- however remember that deploy_stack.py deploys JSON templates rather than YAML; YAML are simply dumped to tmp for convenience and debugging
- reasonable confidence that local JSON parser will handle these single quotes well, and that whatever parses the JSON on the AWS side will do also
- much less confidence about this on the YAML side; but if you ever do need to try and ensure compliance between local and remote YAML parsers, try ruamel.yaml in place of pyyaml
"""

from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

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
    resourcename=H("%s-api-rest-api" % api["name"])
    name={"Fn::Sub": "%s-api-rest-api-${AWS::StackName}" % api["name"]}
    props={"Name": name}
    return (resourcename,            
            "AWS::ApiGateway::RestApi",
            props)

"""
- if you fail to depend on any methods then you get the following 
-  Resource handler returned message: "The REST API doesn't contain any methods (Service: ApiGateway, Status Code: 400, Request ID: 7e343643-cdff-4ca4-9c2f-f94b1b61be5e, Extended Request ID: null)" (RequestToken: ea5517dd-42b4-7e4a-d443-eb3511f34ff5, HandlerErrorCode: InvalidRequest)
"""

@resource
def init_deployment(api, endpoints):
    resourcename=H("%s-api-deployment" % api["name"])
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    depends=[]
    for endpoint in endpoints:
        depends+=[H("%s-api-method" % endpoint["name"]),
                  H("%s-api-cors-method" % endpoint["name"])]
    return (resourcename,            
            "AWS::ApiGateway::Deployment",
            props,
            depends)

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
    providerarn={"Fn::GetAtt": [H("%s-userpool" % api["userpool"]), "Arn"]}
    props={"IdentitySource": "method.request.header.Authorization",
           "Name": name,
           "ProviderARNs": [providerarn],
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
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
    resourcename=H("%s-api-cors-default-%s" % (api["name"], code))
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "ResponseType": "DEFAULT_%s" % code,
           "ResponseParameters": params}
    return (resourcename,
            "AWS::ApiGateway::GatewayResponse",
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

def init_method(api, endpoint, authorisation):
    resourcename=H("%s-api-method" % endpoint["name"])
    uri={"Fn::Sub": [MethodArn, {"arn": {"Fn::GetAtt": [H("%s-function" % endpoint["action"]), "Arn"]}}]}
    integration={"IntegrationHttpMethod": "POST",
                 "Type": "AWS_PROXY",
                 "Uri": uri}
    props={"HttpMethod": endpoint["method"],
           "Integration": integration,
           "ResourceId": {"Ref": H("%s-api-resource" % endpoint["name"])},
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    props.update(authorisation)
    if "parameters" in endpoint:
        props["RequestValidatorId"]={"Ref": H("%s-api-validator" % endpoint["name"])}
        props["RequestParameters"]={"method.request.querystring.%s" % param: True
                                    for param in endpoint["parameters"]}
    elif "schema" in endpoint:
        props["RequestValidatorId"]={"Ref": H("%s-api-validator" % endpoint["name"])}
        props["RequestModels"]={"application/json": H("%s-api-model" % endpoint["name"])}
    return (resourcename,
            "AWS::ApiGateway::Method",
            props)

@resource
def init_simple_method(api, endpoint):
    authorisation={"AuthorizationType": "NONE"}
    return init_method(api, endpoint, authorisation)

@resource
def init_cognito_method(api, endpoint):
    authorisation={"AuthorizationType": "COGNITO_USER_POOLS",
                   "AuthorizerId": {"Ref": H("%s-api-authorizer" % api["name"])}}
    return init_method(api, endpoint, authorisation)

@resource
def init_cors_method(api, endpoint):
    def init_integration_response(endpoint):
        params={CorsMethodHeader % k.capitalize(): "'%s'" % v # NB quotes
                for k, v in [("headers", ",".join(CorsHeaders)),
                             ("methods", "%s,OPTIONS" % endpoint["method"]),
                             ("origin", "*")]}
        templates={"application/json": ""}
        return {"StatusCode": 200,
                "ResponseParameters": params,
                "ResponseTemplates": templates}
    def init_integration(endpoint):
        templates={"application/json": json.dumps({"statusCode": 200})}
        response=init_integration_response(endpoint)
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
    resourcename=H("%s-api-cors-method" % endpoint["name"])
    integration=init_integration(endpoint)
    response=init_response()
    props={"AuthorizationType": "NONE",
           "HttpMethod": "OPTIONS",
           "Integration": integration,
           "MethodResponses": [response],
           "ResourceId": {"Ref": H("%s-api-resource" % endpoint["name"])},
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Method",
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

@resource
def init_validator(api, endpoint):
    resourcename=H("%s-api-validator" % endpoint["name"])
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    if "parameters" in endpoint:
        props["ValidateRequestParameters"]=True
    elif "schema" in endpoint:
        props["ValidateRequestBody"]=True
    return (resourcename,
            "AWS::ApiGateway::RequestValidator",
            props)

"""
- Name is "optional" but is in fact required if Method is to be able to look up model :/
"""

@resource
def init_model(api, endpoint):
    resourcename=H("%s-api-model" % endpoint["name"])
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "ContentType": "application/json",
           "Name": resourcename,
           "Schema": endpoint["schema"]}
    return (resourcename,
            "AWS::ApiGateway::Model",
            props)    

def init_simple_resources(api, endpoints, resources):
    resources.append(init_rest_api(api))
    resources.append(init_deployment(api, endpoints))
    resources.append(init_stage(api))
    for code in "4XX|5XX".split("|"):
        resources.append(init_default_response(api, code))
    for endpoint in endpoints:
        for fn in [init_resource,
                   init_simple_method,
                   init_permission,
                   init_cors_method]:
            resource=fn(api, endpoint)
            resources.append(resource)
        if "parameters" in endpoint:
            resources.append(init_validator(api, endpoint))
        elif "schema" in endpoint:
            resources.append(init_validator(api, endpoint))
            resources.append(init_model(api, endpoint))

def init_cognito_resources(api, endpoints, resources):
    resources.append(init_rest_api(api))
    resources.append(init_deployment(api, endpoints))
    resources.append(init_stage(api))
    resources.append(init_cognito_authorizer(api))    
    for code in "4XX|5XX".split("|"):
        resources.append(init_default_response(api, code))
    for endpoint in endpoints:
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

def init_resources(md):
    endpoints={endpoint["name"]: endpoint
               for endpoint in md.endpoints}
    resources=[]
    for api in md.apis:
        apiendpoints=[endpoints[name]
                      for name in api["endpoints"]]
        if api["type"]=="simple":
            init_simple_resources(api, apiendpoints, resources)
        elif api["type"]=="cognito":
            init_cognito_resources(api, apiendpoints, resources)
        else:
            raise RuntimeError("%s api type '%s' not recognised" % (api["name"], api["type"]))
    return dict(resources)

"""
- RestApi and Stage (echoed from input) are required for apigw redeployment
"""

def init_outputs(md):
    def init_outputs(api, outputs):
        endpoint={"Fn::Sub": EndpointUrl % (H("%s-api-rest-api" % api["name"]),
                                            H("%s-api-stage" % api["name"]))}
        restapi={"Ref": H("%s-api-rest-api" % api["name"])}
        stage={"Ref": H("%s-api-stage" % api["name"])}    
        outputs.update({H("%s-api-endpoint" % api["name"]): {"Value": endpoint},
                        H("%s-api-rest-api" % api["name"]): {"Value": restapi},
                        H("%s-api-stage" % api["name"]): {"Value": stage}})
    outputs={}
    for api in md.apis:
        init_outputs(api, outputs)
    return outputs

def update_template(template, md):
    template.resources.update(init_resources(md))
    template.outputs.update(init_outputs(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("api")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()        
        md.validate().expand()
        update_template(template, md)
        template.dump(template.filename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
