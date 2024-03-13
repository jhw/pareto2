from pareto2.services import hungarorise as H
from pareto2.services import AltNamespaceMixin

from pareto2.services.apigateway import *
from pareto2.services.cognito import *
from pareto2.services.iam import *
from pareto2.services.route53 import *

# from pareto2.services.lambda import Permission as PermissionBase

import importlib
lambda_module = importlib.import_module("pareto2.services.lambda")
Function = lambda_module.InlineFunction
PermissionBase = lambda_module.Permission

from pareto2.recipes import Recipe

import re

def identity_pool_role_condition(namespace, typestr):
    return {"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
            "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}

class IdentityPoolRoleBase(AltNamespaceMixin, Role):

    def __init__(self, namespace, **kwargs):
        super().__init__(namespace, **kwargs)

class IdentityPoolUnauthorizedRole(IdentityPoolRoleBase):

    def __init__(self, namespace):
        super().__init__(namespace,
                         action = "sts:AssumeRoleWithWebIdentity",
                         condition = identity_pool_role_condition(namespace,
                                                                  typestr = "unauthorized"),
                         principal = {"Federated": "cognito-identity.amazonaws.com"},
                         permissions = ["mobileanalytics:PutEvents",
                                        "cognito-sync:*"])

class IdentityPoolAuthorizedRole(IdentityPoolRoleBase):

    def __init__(self, namespace):
        super().__init__(namespace,
                         action = "sts:AssumeRoleWithWebIdentity",
                         condition = identity_pool_role_condition(namespace,
                                                                  typestr = "authorized"),
                         principal = {"Federated": "cognito-identity.amazonaws.com"},
                         permissions = ["mobileanalytics:PutEvents",
                                        "cognito-sync:*",
                                        "cognito-identity:*",
                                        "lambda:InvokeFunction"])

class Permission(PermissionBase):
    
    def __init__(self, namespace, parent_namespace, function_namespace, method, path):
        restapiref, stageref = H(f"{parent_namespace}-rest-api"), H(f"{parent_namespace}-stage")
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{restapiref}}}/${{{stageref}}}/{method}/{path}"}
        super().__init__(namespace = namespace,
                         function_namespace = function_namespace,
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
                      IdentityPoolUnauthorizedRole,
                      IdentityPoolAuthorizedRole,
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

    def function_kwargs(self, endpoint):
        kwargs = {}
        for attr in ["code"]:
            kwargs[attr] = endpoint[attr]
        for attr in ["memory",
                     "timeout",
                     "runtime",
                     "layers"]:
            if attr in endpoint:
                kwargs[attr] = endpoint[attr]
        return kwargs
    
    def role_permissions(self, endpoint,
                         defaults = ["logs:CreateLogGroup",
                                     "logs:CreateLogStream",
                                     "logs:PutLogEvents"]):
        permissions = set(defaults)
        if "permissions" in endpoint:
            permissions.update(set(endpoint["permissions"]))
        return sorted(list(permissions))
    
    def init_endpoint(self, parent_ns, endpoint):
        child_ns = self.endpoint_namespace(parent_ns, endpoint)
        self.append(LambdaProxyResource(namespace = child_ns,
                                        parent_namespace = parent_ns,
                                        path = endpoint["path"]))
        if "parameters" in endpoint:
            self.init_GET_endpoint(parent_ns, child_ns, endpoint)
        elif "schema" in endpoint:
            self.init_POST_endpoint(parent_ns, child_ns, endpoint)
        self.append(Function(namespace = child_ns,
                             **self.function_kwargs(endpoint)))
        self.append(Role(namespace = child_ns,
                         permissions = self.role_permissions(endpoint)))
        self.append(Permission(namespace = child_ns,
                               parent_namespace = parent_ns,
                               function_namespace = child_ns,
                               method = endpoint["method"],
                               path = endpoint["path"]))
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

    
