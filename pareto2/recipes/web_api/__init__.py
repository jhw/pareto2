from pareto2.services import hungarorise as H
from pareto2.services.apigatewayv2 import *
from pareto2.services.cognito import *
from pareto2.services.iam import *
from pareto2.services.route53 import *
from pareto2.recipes import *
from pareto2.recipes.mixins.alerts import AlertsMixin

import importlib, json, re

L = importlib.import_module("pareto2.services.lambda")

"""
You shouldn't need to attach alerts to Cognito lambdas as they are all executed synchronously
"""

class CognitoHookRole(Role):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace)

class CustomAttributesFunction(L.InlineFunction):
    
    def __init__(self, namespace, attributes):
        with open("/".join(__file__.split("/")[:-1]+["/inline_code/custom_attributes.py"])) as f:
            code = f.read()
        super().__init__(namespace = namespace,
                         code = code,
                         variables = {"user-custom-attributes": json.dumps(attributes)})

class CustomAttributesPolicy(Policy):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         permissions = [{"action": ["logs:CreateLogGroup",
                                                    "logs:CreateLogStream",
                                                    "logs:PutLogEvents"]},
                                        {"action": "cognito-idp:AdminUpdateUserAttributes"}])


class CognitoPermission(L.Permission):

    def __init__(self, namespace, userpool_namespace):
        source_arn = {"Fn::GetAtt": [H(f"{userpool_namespace}-user-pool"), "Arn"]}
        super().__init__(namespace = namespace,    
                         source_arn = source_arn,
                         principal = "cognito-idp.amazonaws.com")
        
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

class EndpointPermission(L.Permission):

    def __init__(self, namespace, function_namespace, method, path):
        api_ref, stage_ref = H(f"{namespace}-api"), H(f"{namespace}-stage"), 
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{api_ref}}}/${{{stage_ref}}}/{method}/{path}"}
        super().__init__(namespace = function_namespace,    
                         source_arn = source_arn,
                         principal = "apigateway.amazonaws.com")
    
class WebApi(AlertsMixin):    

    def __init__(self, namespace, endpoints, userpool):
        super().__init__()
        self.init_api_base(namespace = namespace)
        if self.has_private_endpoint(endpoints):
            self.init_private_api(namespace = namespace,
                                  userpool = userpool)
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
        
    def init_private_api(self, namespace, userpool):
        self.append(SimpleEmailUserPool(namespace = namespace,
                                        attributes = userpool["attributes"]))
        for klass in [Authorizer,
                      UserPoolClient,
                      IdentityPool,
                      IdentityPoolAuthenticatedRole,
                      IdentityPoolAuthenticatedPolicy,
                      IdentityPoolUnauthenticatedRole,
                      IdentityPoolUnauthenticatedPolicy,
                      IdentityPoolRoleAttachment]:
            self.append(klass(namespace = namespace))
        # custom attributes
        custom_attributes_namespace = f"{namespace}-custom-attributes"
        self.append(CognitoPermission(namespace = custom_attributes_namespace,
                                      userpool_namespace = namespace))
        self.append(CustomAttributesFunction(namespace = custom_attributes_namespace,
                                             attributes = userpool["attributes"]))
        for klass in [CognitoHookRole,
                      CustomAttributesPolicy]:
            self.append(klass(namespace = custom_attributes_namespace))

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
                 EndpointPermission(namespace = api_namespace,
                                    function_namespace = endpoint_namespace,
                                    method = endpoint["method"],
                                    path = endpoint["path"])]
        self.init_alert_hooks(namespace = endpoint_namespace,
                              log_levels = log_levels)


if __name__ == "__main__":
    pass

    
