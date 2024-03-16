from pareto2.ingredients.apigateway import Resource, Method

class S3ProxyResource(Resource):

    def __init__(self, namespace, path = "{proxy+}"):
        super().__init__(namespace, path)
    
class S3ProxyMethod(Method):

    def __init__(self, namespace):
        super().__init__(namespace)

    @property
    def _integration(self):
        uri = {"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:s3:path/${%s}/{proxy}" % H(f"{self.namespace}-bucket")}
        credentials = {"Fn::GetAtt": [H(f"{self.namespace}-role"), "Arn"]}
        request_parameters = {"integration.request.path.proxy": "method.request.path.proxy"}
        integration_responses = [{"StatusCode": 200,
                                  "ResponseParameters": {"method.response.header.Content-Type": "integration.response.header.Content-Type"}},
                                 {"StatusCode": 404,
                                  "SelectionPattern": "404"}]
        return {"IntegrationHttpMethod": "ANY",
                "Type": "AWS",
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "Uri": uri,
                "Credentials": credentials,
                "RequestParameters": request_parameters, 
                "IntegrationResponses": integration_responses}    
        
    @property
    def aws_properties(self):
        request_parameters = {"method.request.path.proxy": True}
        method_responses = [{"StatusCode": 200,
                             "ResponseParameters": {"method.response.header.Content-Type": True}},
                            {"StatusCode": 404}]
        return {"HttpMethod": "GET",
                "AuthorizationType": "NONE",
                "RequestParameters": request_parameters,
                "MethodResponses": method_responses,
                "Integration": self._integration,
                "ResourceId": {"Ref": H(f"{self.namespace}-resource")},
                "RestApiId": {"Ref": H(f"{self.namespace}-rest-api")}}

