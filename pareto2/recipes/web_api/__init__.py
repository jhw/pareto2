from pareto2.services import hungarorise as H
from pareto2.services.apigatewayv2 import *
from pareto2.services.cognito import *
from pareto2.services.iam import *
from pareto2.services.route53 import *
from pareto2.recipes import *
from pareto2.recipes.mixins.alerts import AlertsMixin

import importlib, re

L = importlib.import_module("pareto2.services.lambda")

"""
Congito callback functions do not have alerts attached as the event messages do not have any user component so should always (??) fit inside the 256K EventBridge lmiit
"""

class UserCallbackFunction(L.InlineFunction):
    
    def __init__(self, namespace, userpool_namespace):
        with open("/".join(__file__.split("/")[:-1]+["/inline_code/user_callback.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"app-user-pool": {"Ref": H(f"{userpool_namespace}-user-pool")}})

class UserCallbackRole(Role):
    
    def __init__(self, namespace, **kwargs):
        super().__init__(namespace = namespace)
        
class UserCallbackPolicy(Policy):
    
    def __init__(self, namespace, **kwargs):
        super().__init__(namespace = namespace,
                         permissions = [{"action": "events:PutEvents"},
                                        {"action": ["logs:CreateLogGroup",
                                                    "logs:CreateLogStream",
                                                    "logs:PutLogEvents"]}])

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

class LambdaPermission(L.Permission):

    def __init__(self, namespace, function_namespace, method, path):
        api_ref, stage_ref = H(f"{namespace}-api"), H(f"{namespace}-stage"), 
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{api_ref}}}/${{{stage_ref}}}/{method}/{path}"}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "apigateway.amazonaws.com")
    
class WebApi(AlertsMixin):    

    def __init__(self, namespace, endpoints):
        super().__init__()
        self.init_api_base(namespace = namespace)
        if self.has_private_endpoint(endpoints):
            self.init_private_api(namespace = namespace)
        for endpoint in endpoints:
            self.init_endpoint(api_namespace = namespace,
                               endpoint = endpoint)
        self.init_alert_resources()

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
                      RegionalRecordSet]: # NB
            self.append(klass(namespace = namespace))
        
    def init_private_api(self, namespace):
        for klass in [Authorizer,
                      SimpleEmailUserPool,
                      UserPoolClient,
                      IdentityPool,
                      IdentityPoolAuthenticatedRole,
                      IdentityPoolAuthenticatedPolicy,
                      IdentityPoolUnauthenticatedRole,
                      IdentityPoolUnauthenticatedPolicy,
                      IdentityPoolRoleAttachment]:
            self.append(klass(namespace = namespace))
        callback_namespace = f"{namespace}-user-callback"  
        for klass in [UserCallbackFunction,
                      UserCallbackRole,
                      UserCallbackPolicy]:
            self.append(klass(namespace = callback_namespace,
                              userpool_namespace = namespace))


    def endpoint_namespace(self, namespace, endpoint):
        return "%s-%s" % (namespace,
                          "-".join([tok.lower()
                                    for tok in re.split("\\W", endpoint["path"])
                                    if tok != ""]))
    
    def init_endpoint(self,
                      api_namespace,
                      endpoint,
                      log_levels = ["warning", "error"]):
        endpoint_namespace = self.endpoint_namespace(api_namespace, endpoint)
        routeclass = eval("%sRoute" % endpoint["auth"].capitalize())
        fn = L.InlineFunction if "code" in endpoint else L.S3Function
        self += [routeclass(namespace = endpoint_namespace,
                            api_namespace = api_namespace,
                            endpoint = endpoint),
                 Integration(namespace = endpoint_namespace,
                             api_namespace = api_namespace),
                 fn(namespace = endpoint_namespace,
                    **function_kwargs(endpoint)),
                 Role(namespace = endpoint_namespace),
                 Policy(namespace = endpoint_namespace,
                        permissions = policy_permissions(endpoint)),
                 LambdaPermission(namespace = api_namespace,
                                  function_namespace = endpoint_namespace,
                                  method = endpoint["method"],
                                  path = endpoint["path"])]
        self.init_alert_hooks(namespace = endpoint_namespace,
                              log_levels = log_levels)


if __name__ == "__main__":
    pass

    
