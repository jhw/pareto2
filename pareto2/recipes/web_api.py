from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.apigateway import *
from pareto2.ingredients.apigateway.cors import *
from pareto2.ingredients.cognito import *
from pareto2.ingredients.iam import *
from pareto2.ingredients.route53 import *

from pareto2.recipes import Recipe

import importlib, re

lambda_module = importlib.import_module("pareto2.ingredients.lambda")
apigateway_lambda_module = importlib.import_module("pareto2.ingredients.apigateway.lambda")

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
        self.append(apigateway_lambda_module.LambdaResource(namespace = child_ns,
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
        methodfn = eval("apigateway_lambda_module.%s" % H(f"{self.auth}-lambda-proxy-method"))
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
        methodfn = eval("apigateway_lambda_module.%s" % H(f"{self.auth}-lambda-proxy-method"))
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
        return apigateway_lambda_module.LambdaProxyPermission(namespace = parent_ns,
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

    
