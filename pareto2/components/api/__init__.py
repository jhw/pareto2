from pareot2.aws.apigateway import Resource as ResourceBase
from pareot2.aws.apigateway import RestApi as RestApiBase
from pareot2.aws.apigateway import Stage as StageBase
from pareto2.aws.lambda import Permission as PermissionBase

class RestApi(RestApiBase):

    def __init__(self, api):
        super().__init__(api["name"])

class Stage(StageBase):
    
    def __init__(self, api):
        super().__init__(api["name"], api["stage"]["name"], f"{api['name']}-api-deployment", f"{api['name']}-api-rest-api")


class Resource(ResourceBase):

    def __init__(self, api, endpoint):
        super().__init__(endpoint["name"], f"{api['name']}-api-rest-api", endpoint["path"])


class Permission(PermissionBase):
    
    def __init__(self, api, endpoint):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{api['name']}/{endpoint['method']}/{endpoint['path']}"}
        super().__init__(endpoint["name"],
                         endpoint["action"],
                         source_arn,
                         "apigateway.amazonaws.com")
