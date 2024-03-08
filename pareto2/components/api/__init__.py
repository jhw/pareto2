class Method(MethodBase):

    def __init__(self, api):
        super().__init__(api)

    @property
    def resource_name(self):
        return f"{self.api['name']}-api-method"

    @property
    def aws_properties(self):
        integration = self.init_integration()
        reqparams = {"method.request.path.proxy": True}
        methodresponses = [
            {"StatusCode": 200, "ResponseParameters": {"method.response.header.Content-Type": True}},
            {"StatusCode": 404}
        ]
        return {
            "HttpMethod": "GET",
            "AuthorizationType": "NONE",
            "RequestParameters": reqparams,
            "MethodResponses": methodresponses,
            "Integration": integration,
            "ResourceId": {"Ref": f"{self.api['name']}-api-resource"},
            "RestApiId": {"Ref": f"{self.api['name']}-api-rest-api"}
        }

    def init_integration(self):
        uri = {"Fn::Sub": f"arn:aws:apigateway:${{AWS::Region}}:s3:path/${{{self.api['name']}-api}}/{{proxy}}"}
        creds = {"Fn::GetAtt": [f"{self.api['name']}-api-role", "Arn"]}
        reqparams = {"integration.request.path.proxy": "method.request.path.proxy"}
        responses = [
            {"StatusCode": 200, "ResponseParameters": {"method.response.header.Content-Type": "integration.response.header.Content-Type"}},
            {"StatusCode": 404, "SelectionPattern": "404"}
        ]
        return {
            "IntegrationHttpMethod": "ANY",
            "Type": "AWS",
            "PassthroughBehavior": "WHEN_NO_MATCH",
            "Uri": uri,
            "Credentials": creds,
            "RequestParameters": reqparams,
            "IntegrationResponses": responses
        }
    
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
