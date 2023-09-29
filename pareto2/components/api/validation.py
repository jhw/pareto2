from pareto2.components import hungarorise as H
from pareto2.components import resource

EndpointSchemaVersion="http://json-schema.org/draft-07/schema#"

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
def init_model(api, endpoint, schematype=EndpointSchemaVersion):
    resourcename=H("%s-api-model" % endpoint["name"])
    schema=endpoint["schema"]
    if "$schema" not in schema:
        schema["$schema"]=schematype
    props={"RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "ContentType": "application/json",
           "Name": resourcename,
           "Schema": schema}
    return (resourcename,
            "AWS::ApiGateway::Model",
            props)    

if __name__=="__main__":
    pass
