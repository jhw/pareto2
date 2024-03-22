from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.apigateway import Method

import json

CorsHeaders = ["Content-Type",
               "X-Amz-Date",
               "Authorization",
               "X-Api-Key",
               "X-Amz-Sec"]

"""
If a Lambda function is exposed to the web via LambdaMethod and the endpoint to which this method is bound is CORS- enabled using CorsMethod, then the Lambda function *must* return the following additional headers if CORS is to work properly -

- "Access-Control-Allow-Origin": "*"
- "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
- Access-Control-Allow-Methods": "OPTIONS,GET" // change second of these according to LambdaMethod HTTP method

(see also response format required by LambdaMethod)
"""

class CorsMethod(Method):

    def __init__(self, namespace, parent_namespace, method):
        super().__init__(namespace = namespace)
        self.parent_namespace = parent_namespace
        self.method = method

    @property
    def _integration_response(self, cors_headers = CorsHeaders):
        parameters = {"method.response.header.Access-Control-Allow-%s" % k.capitalize(): "'%s'" % v # NB quotes
                      for k, v in [("headers", ",".join(cors_headers)),
                                   ("methods", f"{self.method},OPTIONS"),
                                   ("origin", "*")]}
        templates = {"application/json": ""}
        return {"StatusCode": 200,
                "ResponseParameters": parameters,
                "ResponseTemplates": templates}

    @property
    def _integration(self):
        templates = {"application/json": json.dumps({"statusCode": 200})}
        return {"IntegrationResponses": [self._integration_response],
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "RequestTemplates": templates,
                "Type": "MOCK"}

    @property
    def _method_responses(self):
        response_parameters = {"method.response.header.Access-Control-Allow-%s" % k.capitalize(): False
                               for k in ["headers", "methods", "origin"]}
        response_models = {"application/json": "Empty"}
        return [{"StatusCode": 200,
                 "ResponseModels": response_models,
                 "ResponseParameters": response_parameters}]
        
    @property
    def aws_properties(self):
        return {"AuthorizationType": "NONE",
                "HttpMethod": "OPTIONS",
                "Integration": self._integration,
                "MethodResponses": self._method_responses,
                "ResourceId": {"Ref": H(f"{self.namespace}-resource")},
                "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")}}

