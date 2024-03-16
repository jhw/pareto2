from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.apigateway import Resource, Method

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

LambdaProxyMethodArn = "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

"""
- LambdaProxyResource doesn't use namespace directly, but still needs to live in its own namespace because a single API might have multiple endpoints, each with their own resources
"""
        
class LambdaProxyResource(Resource):

    def __init__(self, namespace, parent_namespace, path):
        super().__init__(namespace, path)
        self.parent_namespace = parent_namespace
        
    @property
    def aws_properties(self):
        return {
            "ParentId": {"Fn::GetAtt": [H(f"{self.parent_namespace}-rest-api"), "RootResourceId"]},
            "PathPart": self.path,
            "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")}
        }

class LambdaProxyMethod(Method):

    def __init__(self,
                 namespace,
                 parent_namespace,
                 function_namespace,
                 method,
                 authorisation = None,
                 parameters = None,
                 schema = None):
        super().__init__(namespace)
        self.parent_namespace = parent_namespace
        self.function_namespace = function_namespace
        self.method = method
        self.authorisation = authorisation
        self.parameters = parameters
        self.schema = schema
        
    @property
    def aws_properties(self):
        uri = {"Fn::Sub": [LambdaProxyMethodArn, {"arn": {"Fn::GetAtt": [H(f"{self.function_namespace}-function"), "Arn"]}}]}
        integration = {"IntegrationHttpMethod": "POST",
                       "Type": "AWS_PROXY",
                       "Uri": uri}
        props = {"HttpMethod": self.method,
                 "Integration": integration,
                 "ResourceId": {"Ref": H(f"{self.namespace}-resource")},
                 "RestApiId": {"Ref": H(f"{self.parent_namespace}-rest-api")}}
        props.update(self.authorisation)
        if self.parameters:
            props["RequestValidatorId"] = {"Ref": H(f"{self.namespace}-parameter-request-validator")}
            props["RequestParameters"] = {f"method.request.querystring.{param}": True
                                        for param in self.parameters}
        if self.schema:
            props["RequestValidatorId"] = {"Ref": H(f"{self.namespace}-schema-request-validator")}
            props["RequestModels"] = {"application/json": H(f"{self.namespace}-model")}
        return props

class PublicLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "NONE"},
                         **kwargs)

class PrivateLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "COGNITO_USER_POOLS",
                                          "AuthorizerId": {"Ref": H(f"{parent_namespace}-authorizer")}},
                         **kwargs)

class LambdaProxyPermission(lambda_module.Permission):

    def __init__(self, namespace, function_namespace, method, path):
        restapiref, stageref = H(f"{namespace}-rest-api"), H(f"{namespace}-stage")
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{restapiref}}}/${{{stageref}}}/{method}/{path}"}
        super().__init__(namespace = function_namespace,    
                         function_namespace = function_namespace,
                         source_arn = source_arn,
                         principal = "apigateway.amazonaws.com")
