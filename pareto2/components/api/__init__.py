from pareto2.aws.apigateway import BasePathMapping as BasePathMappingBase
from pareto2.aws.apigateway import DomainName as DomainNameBase
from pareto2.aws.apigateway import RestApi as RestApiBase
from pareto2.aws.apigateway import Deployent as DeploymentBase
from pareto2.aws.apigateway import Stage as StageBase
from pareto2.aws.apigateway import Resource as ResourceBase
from pareto2.aws.apigateway import Method as MethodBase

from pareto.aws.iam import Role as RoleBase

from pareto2.aws.lambda import Permission as PermissionBase

from pareto2.aws.route53 import RecordSet as RecordSetBase

class RestApi(RestApiBase):

    def __init__(self, api):
        super().__init__(api["name"])

class CorsDeployment(DeploymentBase):

    def __init__(self, api):
        super().__init__(api["name"])
        self.api = api

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": f"{self.name}-api-rest-api"}
        }

    @property
    def depends(self):
        dependencies = []
        for endpoint in self.api["endpoints"]:
            dependencies += [f"{endpoint['name']}-api-method", f"{endpoint['name']}-api-cors-method"]
        return dependencies
        
class Stage(StageBase):
    
    def __init__(self, api):
        super().__init__(api["name"], api["stage"]["name"], f"{api['name']}-api-deployment", f"{api['name']}-api-rest-api")


class Resource(ResourceBase):

    def __init__(self, api, endpoint):
        super().__init__(endpoint["name"], f"{api['name']}-api-rest-api", endpoint["path"])

class CorsMethod(MethodBase):
    
    def __init__(self, api, endpoint, **kwargs):
        super().__init__(endpoint["name"], **kwargs)
        self.api = api
        self.endpoint = endpoint

    @property
    def aws_properties(self):
        def init_integration_response(endpoint):
            params = {k.capitalize(): "'%s'" % v for k, v in [
                ("headers", ",".join(["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"])),
                ("methods", f"{endpoint['method']},OPTIONS"),
                ("origin", "*")
            ]}
            templates = {"application/json": ""}
            return {"StatusCode": 200, "ResponseParameters": params, "ResponseTemplates": templates}

        integration_response = init_integration_response(self.endpoint)
        integration

class DomainName(DomainNameBase):

    def __init__(self, api):
        super().__init__(api["name"])

class BasePathMapping(BasePathMappingBase):

    def __init__(self, api):
        super().__init__(api["name"], "domain-name", api["stage"]["name"])
        self.api = api

class RecordSet(RecordSetBase):

    def __init__(self, api):
        super().__init__(api["name"], "api")
        
class Permission(PermissionBase):
    
    def __init__(self, api, endpoint):
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:{api['name']}/{endpoint['method']}/{endpoint['path']}"}
        super().__init__(endpoint["name"],
                         endpoint["action"],
                         source_arn,
                         "apigateway.amazonaws.com")

class IdentityPoolUnauthorizedRole(RoleBase):

    def __init__(self, api, permissions=None):
        super().__init__(api["name"],
                         permissions or ["mobileanalytics:PutEvents",
                                         "cognito-sync:*"])
        
class IdentityPoolAuthorizedRole(RoleBase):

    def __init__(self, api, permissions=None):
        super().__init__(api["name"],
                         permissions or ["mobileanalytics:PutEvents",
                                         "cognito-sync:*",
                                         "cognito-identity:*",
                                         "lambda:InvokeFunction"])
