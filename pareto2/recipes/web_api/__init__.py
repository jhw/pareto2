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
        api_ref, stage_ref = H(f"{namespace}-api"), H(f"{namespace}-stage"), 
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{api_ref}}}/${{{stage_ref}}}/{method}/{path}"}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "apigateway.amazonaws.com")
        
class PublicRoute(Route):

    def __init__(self, namespace, api_namespace, endpoint):
        super().__init__(namespace = namespace,
                         api_namespace = api_namespace,
                         endpoint = endpoint)

    @property
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "AuthorizationType": "NONE"
        })
        return props
        
class PrivateRoute(Route):

    def __init__(self, namespace, api_namespace, endpoint):
        super().__init__(namespace = namespace,
                         api_namespace = api_namespace,
                         endpoint = endpoint)

    @property
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "AuthorizationType": "JWT",
            "AuthorizerId": {"Ref": H(f"{self.api_namespace}-authorizer")}
        })
        return props
                
class WebApi(Recipe):    

    def __init__(self, namespace, endpoints):
        super().__init__()
        self.init_api_base(namespace = namespace)
        if self.has_private_endpoint(endpoints):
            self.init_private_api(namespace = namespace)
        for endpoint in endpoints:
            self.init_endpoint(api_namespace = namespace,
                               endpoint = endpoint)

    def has_private_endpoint(self, endpoints):
        for endpoint in endpoints:
            if endpoint["auth"] == "private":
                return True
        return False
        
    def init_api_base(self, namespace):
        for klass in [Api,
                      Stage,
                      DomainName,
                      ApiMapping,
                      RecordSet]:
            self.append(klass(namespace = namespace))
        
    def init_private_api(self, namespace):
        for klass in [Authorizer,
                      SimpleEmailUserPool,
                      UserPoolClient,
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
    
    def init_endpoint(self, api_namespace, endpoint):
        endpoint_namespace = self.endpoint_namespace(api_namespace, endpoint)
        routeclass = eval("%sRoute" % endpoint["auth"].capitalize())
        self.append(routeclass(namespace = endpoint_namespace,
                               api_namespace = api_namespace,
                               endpoint = endpoint))
        self.append(Integration(namespace = endpoint_namespace,
                                api_namespace = api_namespace))
        self.append(self.init_function(namespace = endpoint_namespace,
                                       endpoint = endpoint))
        self += self.init_role_and_policy(namespace = endpoint_namespace,
                                          endpoint = endpoint)
        self.append(self.init_lambda_permission(api_namespace = api_namespace,
                                                endpoint_namespace = endpoint_namespace,
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
    
    def init_lambda_permission(self, api_namespace, endpoint_namespace, endpoint):
        return LambdaPermission(namespace = api_namespace,
                                function_namespace = endpoint_namespace,
                                method = endpoint["method"],
                                path = endpoint["path"])

if __name__ == "__main__":
    pass

    
