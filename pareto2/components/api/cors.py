from pareto2.components import hungarorise as H
from pareto2.components import resource

import json, yaml

CorsGatewayHeader="gatewayresponse.header.Access-Control-Allow-%s"

CorsMethodHeader="method.response.header.Access-Control-Allow-%s"

CorsHeaders=yaml.safe_load("""
- Content-Type
- X-Amz-Date
- Authorization
- X-Api-Key
- X-Amz-Security-Token
""")

@resource
def init_cors_deployment(api):
    resourcename=H("%s-api-deployment" % api["name"])
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])}}
    depends=[]
    for endpoint in api["endpoints"]:
        depends+=[H("%s-api-method" % endpoint["name"]),
                  H("%s-api-cors-method" % endpoint["name"])]
    return (resourcename,            
            "AWS::ApiGateway::Deployment",
            props,
            depends)

"""
- https://serverless-stack.com/chapters/handle-api-gateway-cors-errors.html
- otherwise a server error can manifest itself as a CORS error
"""

@resource
def init_cors_default_response(api, code):        
    params={CorsGatewayHeader % k.capitalize(): "'%s'" % v # NB quotes
            for k, v in [("headers", "*"),
                         ("origin", "*")]}
    resourcename=H("%s-api-cors-response-%s" % (api["name"], code))
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "ResponseType": "DEFAULT_%s" % code,
           "ResponseParameters": params}
    return (resourcename,
            "AWS::ApiGateway::GatewayResponse",
            props)

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
