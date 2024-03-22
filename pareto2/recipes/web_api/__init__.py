from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.apigateway import *
from pareto2.ingredients.apigateway import Resource as APIGWResource
from pareto2.ingredients.cognito import *
from pareto2.ingredients.iam import *
from pareto2.ingredients.route53 import *

from pareto2.recipes import Recipe
from pareto2.recipes.web_api.cors import CorsMethod

import importlib, re

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

LambdaMethodArn = "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations"

"""
- LambdaResource doesn't use namespace directly, but still needs to live in its own namespace because a single API might have multiple endpoints, each with their own resources
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

class LambdaMethod(Method):

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
        uri = {"Fn::Sub": [LambdaMethodArn, {"arn": {"Fn::GetAtt": [H(f"{self.function_namespace}-function"), "Arn"]}}]}
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

class PublicLambdaMethod(LambdaMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace = namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "NONE"},
                         **kwargs)

class PrivateLambdaMethod(LambdaMethod):

    def __init__(self, namespace, parent_namespace, **kwargs):
        super().__init__(namespace = namespace,
                         parent_namespace = parent_namespace,
                         authorisation = {"AuthorizationType": "COGNITO_USER_POOLS",
                                          "AuthorizerId": {"Ref": H(f"{parent_namespace}-authorizer")}},
                         **kwargs)

class LambdaPermission(lambda_module.Permission):

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
        methodfn = eval(H(f"{self.auth}-lambda-method"))
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
        methodfn = eval(H(f"{self.auth}-lambda-method"))
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
        return LambdaPermission(namespace = parent_ns,
                                function_namespace = child_ns,
                                method = endpoint["method"],
                                path = endpoint["path"])
        
    def filter_methods(self, parent_ns, endpoints):
        methods = []
        for endpoint in endpoints:
            child_ns = self.endpoint_namespace(parent_ns, endpoint)
            methods += [H(f"{child_ns}-{self.auth}-lambda-method"),
                        H(f"{child_ns}-cors-method")]
        return methods
    
    def init_deployment(self, namespace, methods):
        self.append(Deployment(namespace = namespace,
                               methods = methods))
            
if __name__ == "__main__":
    pass

    
