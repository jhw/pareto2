from pareto2.aws.apigateway import Deployment, Method

class CorsDeployment(Deployment):

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

class CorsMethod(Method):
    
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
