
from pareto2.components import hungarorise as H
from pareto2.components import resource

import json, yaml

MethodArn="arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

CorsMethodHeader="method.response.header.Access-Control-Allow-%s"

CorsHeaders=yaml.safe_load("""
- Content-Type
- X-Amz-Date
- Authorization
- X-Api-Key
- X-Amz-Security-Token
""")

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
def init_open_method(api, endpoint):
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

if __name__=="__main__":
    pass
