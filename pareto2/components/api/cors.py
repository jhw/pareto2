from pareto2.aws.apigateway import Method

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
