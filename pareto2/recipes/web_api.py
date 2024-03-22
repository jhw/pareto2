from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.apigateway import *
from pareto2.ingredients.apigateway import Resource as APIGWResource
from pareto2.ingredients.cognito import *
from pareto2.ingredients.iam import *
from pareto2.ingredients.route53 import *

from pareto2.recipes import Recipe

import importlib, json, re

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

LambdaProxyMethodArn = "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

CorsHeaders = ["Content-Type",
               "X-Amz-Date",
               "Authorization",
               "X-Api-Key",
               "X-Amz-Sec"]

"""
If a Lambda function is exposed to the web via LambdaProxyMethod and the endpoint to which this method is bound is CORS- enabled using CorsMethod, then the Lambda function *must* return the following additional headers if CORS is to work properly -

- "Access-Control-Allow-Origin": "*"
- "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
- Access-Control-Allow-Methods": "OPTIONS,GET" // change second of these according to LambdaProxyMethod HTTP method

(see also response format required by LambdaProxyMethod)
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

"""
- LambdaProxyResource doesn't use namespace directly, but still needs to live in its own namespace because a single API might have multiple endpoints, each with their own resources
"""
        
class LambdaResource(APIGWResource):

    def __init__(self, namespace, parent_namespace, path):
        super().__init__(namespace = namespace,
                         path = path)
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
        super().__init__(namespace = namespace)
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
        super().__init__(namespace = namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "NONE"},
                         **kwargs)

class PrivateLambdaProxyMethod(LambdaProxyMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace = namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "COGNITO_USER_POOLS",
                                          "AuthorizerId": {"Ref": H(f"{parent_namespace}-authorizer")}},
                         **kwargs)

class LambdaProxyPermission(lambda_module.Permission):

    def __init__(self, namespace, function_namespace, method, path):
        restapiref, stageref = H(f"{namespace}-rest-api"), H(f"{namespace}-stage")
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{restapiref}}}/${{{stageref}}}/{method}/{path}"}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "apigateway.amazonaws.com")

class WebApi(Recipe):    

    def __init__(self, namespace, endpoints, auth = "public"):
        super().__init__()
        self.auth = auth
        apifn = getattr(self, f"init_{self.auth}_api")
        apifn(namespace)
        for endpoint in endpoints:
            self.init_endpoint(namespace, endpoint)
        methods = self.filter_methods(namespace, endpoints)
        self.init_deployment(namespace, methods)

    def init_public_api(self, namespace):
        self.init_api_base(namespace)
            
    def init_private_api(self, namespace):
        self.init_api_base(namespace)
        for klass in [Authorizer,
                      SimpleEmailUserPool,
                      UserPoolAdminClient,
                      UserPoolWebClient,
                      IdentityPool,
                      IdentityPoolAuthorizedRole,
                      IdentityPoolAuthorizedPolicy,
                      IdentityPoolUnauthorizedRole,
                      IdentityPoolUnauthorizedPolicy,
                      IdentityPoolRoleAttachment]:
            self.append(klass(namespace = namespace))

    def init_api_base(self, namespace):
        for klass in [RestApi,
                      Stage,
                      GatewayResponse4xx,
                      GatewayResponse5xx,
                      DomainName,
                      BasePathMapping,
                      RecordSet]:
            self.append(klass(namespace = namespace))

    def endpoint_namespace(self, namespace, endpoint):
        return "%s-%s" % (namespace,
                          "-".join([tok.lower()
                                    for tok in re.split("\\W", endpoint["path"])
                                    if tok != ""]))
    
    def init_endpoint(self, parent_ns, endpoint):
        child_ns = self.endpoint_namespace(parent_ns, endpoint)
        self.append(LambdaResource(namespace = child_ns,
                                   parent_namespace = parent_ns,
                                   path = endpoint["path"]))
        if "parameters" in endpoint:
            self.init_GET_endpoint(parent_ns, child_ns, endpoint)
        elif "schema" in endpoint:
            self.init_POST_endpoint(parent_ns, child_ns, endpoint)
        self.append(self.init_function(namespace = child_ns,
                                       endpoint = endpoint))
        self += self.init_role_and_policy(namespace = child_ns,
                                          endpoint = endpoint)
        self.append(self.init_lambda_permission(parent_ns = parent_ns,
                                                child_ns = child_ns,
                                                endpoint = endpoint))
        self.append(CorsMethod(namespace = child_ns,
                               parent_namespace = parent_ns,
                               method = endpoint["method"]))

    def init_GET_endpoint(self, parent_ns, child_ns, endpoint):
        self.append(ParameterRequestValidator(namespace = child_ns,
                                              parent_namespace = parent_ns))
        methodfn = eval(H(f"{self.auth}-lambda-proxy-method"))
        self.append(methodfn(namespace = child_ns,
                             parent_namespace = parent_ns,
                             function_namespace = child_ns,
                             method = endpoint["method"],
                             parameters = endpoint["parameters"]))

    def init_POST_endpoint(self, parent_ns, child_ns, endpoint):
        self.append(SchemaRequestValidator(namespace = child_ns,
                                           parent_namespace = parent_ns))
        self.append(Model(namespace = child_ns,
                          parent_namespace = parent_ns,
                          schema = endpoint["schema"]))
        methodfn = eval(H(f"{self.auth}-lambda-proxy-method"))
        self.append(methodfn(namespace = child_ns,
                             parent_namespace = parent_ns,
                             function_namespace = child_ns, 
                             method = endpoint["method"],
                             schema = endpoint["schema"]))

    def init_function(self, namespace, endpoint):
        fn = lambda_module.InlineFunction if "code" in endpoint else lambda_module.S3Function
        return fn(namespace = namespace,
                  **self.function_kwargs(endpoint))

    def init_role_and_policy(self, namespace, endpoint):
        return [
            Role(namespace),
            Policy(namespace = namespace,
                   permissions = self.policy_permissions(endpoint))
        ]
    
    def init_lambda_permission(self, parent_ns, child_ns, endpoint):
        return LambdaProxyPermission(namespace = parent_ns,
                                     function_namespace = child_ns,
                                     method = endpoint["method"],
                                     path = endpoint["path"])
        
    def filter_methods(self, parent_ns, endpoints):
        methods = []
        for endpoint in endpoints:
            child_ns = self.endpoint_namespace(parent_ns, endpoint)
            methods += [H(f"{child_ns}-{self.auth}-lambda-proxy-method"),
                        H(f"{child_ns}-cors-method")]
        return methods
    
    def init_deployment(self, namespace, methods):
        self.append(Deployment(namespace = namespace,
                               methods = methods))
            
if __name__ == "__main__":
    pass

    
