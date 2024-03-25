from pareto2.services import hungarorise as H

from pareto2.services.apigatewayv2 import *
from pareto2.services.cognito import *
from pareto2.services.iam import *
from pareto2.services.route53 import *

from pareto2.recipes import Recipe

import importlib, re

L = importlib.import_module("pareto2.services.lambda")

class LambdaPermission(L.Permission):

    def __init__(self, namespace, function_namespace, method, path):
        apiref, stageref = H(f"{namespace}-api"), H(f"{namespace}-stage")
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{apiref}}}/${{{stageref}}}/{method}/{path}"}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "apigateway.amazonaws.com")

class WebApi(Recipe):    

    def __init__(self, namespace, endpoints):
        super().__init__()
        self.init_api_base(namespace = namespace)
        if self.has_private_endpoint(endpoints):
            self.init_private_api(namespace = namespace)
        for endpoint in endpoints:
            self.init_endpoint(parent_ns = namespace,
                               endpoint = endpoint)
        methods = self.filter_methods(parent_ns = namespace,
                                      endpoints = endpoints)
        self.init_deployment(namespace = namespace,
                             methods = methods)

    def has_private_endpoint(self, endpoints):
        for endpoint in endpoints:
            if endpoint["auth"] == "private":
                return True
        return False
        
    def init_api_base(self, namespace):
        for klass in [Api,
                      Stage,
                      GatewayResponse4xx,
                      GatewayResponse5xx,
                      DomainName,
                      ApiMapping,
                      RecordSet]:
            self.append(klass(namespace = namespace))
        
    def init_private_api(self, namespace):
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

    def endpoint_namespace(self, namespace, endpoint):
        return "%s-%s" % (namespace,
                          "-".join([tok.lower()
                                    for tok in re.split("\\W", endpoint["path"])
                                    if tok != ""]))
    
    def init_endpoint(self, parent_ns, endpoint):
        child_ns = self.endpoint_namespace(parent_ns, endpoint)
        self.append(self.init_function(namespace = child_ns,
                                       endpoint = endpoint))
        self += self.init_role_and_policy(namespace = child_ns,
                                          endpoint = endpoint)
        self.append(self.init_lambda_permission(parent_ns = parent_ns,
                                                child_ns = child_ns,
                                                endpoint = endpoint))

    def init_function(self, namespace, endpoint):
        fn = L.InlineFunction if "code" in endpoint else L.S3Function
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
            methods += [H(f"{child_ns}-route"),
                        H(f"{child_ns}-integration")]
    
    def init_deployment(self, namespace, methods):
        self.append(Deployment(namespace = namespace,
                               methods = methods))
            
if __name__ == "__main__":
    pass

    
