from pareot2.aws.apigateway import Resource as ResourceBase
from pareto2.aws.lambda import Permission as PermissionBase

class ApiResource(ResourceBase):

    def __init__(self, api, endpoint):
        super().__init__(endpoint["name"], f"{api['name']}-api-rest-api", endpoint["path"])


class APIPermission(PermissionBase):
    
    def __init__(self, api, endpoint):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{api['name']}/{endpoint['method']}/{endpoint['path']}"}
        super().__init__(endpoint["name"],
                         endpoint["action"],
                         source_arn,
                         "apigateway.amazonaws.com")
