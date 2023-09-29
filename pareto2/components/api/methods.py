from pareto2.components import hungarorise as H
from pareto2.components import resource

import json

MethodArn="arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

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

if __name__=="__main__":
    pass
