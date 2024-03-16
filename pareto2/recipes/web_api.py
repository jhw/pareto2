from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import AltNamespaceMixin

from pareto2.ingredients.apigateway import *
from pareto2.ingredients.cognito import *
from pareto2.ingredients.iam import *
from pareto2.ingredients.route53 import *

from pareto2.recipes import Recipe

import importlib, re

lambda_module = importlib.import_module("pareto2.ingredients.lambda")
apigateway_lambda_module = importlib.import_module("pareto2.ingredients.apigateway.lambda")

class IdentityPoolAuthorizedRole(AltNamespaceMixin, Role):

    def __init__(self, namespace, **kwargs):
        super().__init__(namespace, **kwargs)

class IdentityPoolUnauthorizedRole(AltNamespaceMixin, Role):

    def __init__(self, namespace, **kwargs):
        super().__init__(namespace, **kwargs)

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
                      IdentityPoolRoleAttachment]:
            self.append(klass(namespace = namespace))
        self.init_identity_pool_roles(namespace)

    def init_api_base(self, namespace):
        for klass in [RestApi,
                      Stage,
                      GatewayResponse4xx,
                      GatewayResponse5xx,
                      DomainName,
                      BasePathMapping,
                      RecordSet]:
            self.append(klass(namespace = namespace))

    def init_identity_pool_roles(self, namespace, roleconfig = [("unauthorized",
                                                                 ["cognito-sync:*"]),
                                                                ("authorized",
                                                                 ["cognito-sync:*",
                                                                  "cognito-identity:*",
                                                                  "lambda:InvokeFunction"])]):
        for typestr, permissions in roleconfig:            
            condition = {"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{namespace}-identity-pool")}},
                         "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
            klass = eval(H(f"identity-pool-{typestr}-role"))                        
            self.append(klass(namespace = namespace,
                              action = "sts:AssumeRoleWithWebIdentity",
                              condition = condition,
                              principal = {"Federated": "cognito-identity.amazonaws.com"},
                              permissions = permissions))
            
    def endpoint_namespace(self, namespace, endpoint):
        return "%s-%s" % (namespace,
                          "-".join([tok.lower()
                                    for tok in re.split("\\W", endpoint["path"])
                                    if tok != ""]))
    
    def init_endpoint(self, parent_ns, endpoint):
        child_ns = self.endpoint_namespace(parent_ns, endpoint)
        self.append(apigateway_lambda_module.LambdaProxyResource(namespace = child_ns,
                                                                 parent_namespace = parent_ns,
                                                                 path = endpoint["path"]))
        if "parameters" in endpoint:
            self.init_GET_endpoint(parent_ns, child_ns, endpoint)
        elif "schema" in endpoint:
            self.init_POST_endpoint(parent_ns, child_ns, endpoint)
        self.append(self.init_function(namespace = child_ns,
                                       endpoint = endpoint))
        self.append(self.init_role(namespace = child_ns,
                                   endpoint = endpoint))
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

    def function_kwargs(self, endpoint):
        kwargs = {}
        for attr in ["code",
                     "handler",
                     "memory",
                     "timeout",
                     "runtime",
                     "layers"]:
            if attr in endpoint:
                kwargs[attr] = endpoint[attr]
        return kwargs

    def init_function(self, namespace, endpoint):
        fn = lambda_module.InlineFunction if "code" in endpoint else lambda_module.S3Function
        return fn(namespace = namespace,
                  **self.function_kwargs(endpoint))

    def wildcard_override(fn):
        def wrapped(self, *args, **kwargs):
            permissions=fn(self, *args, **kwargs)
            wildcards=set([permission.split(":")[0]
                           for permission in permissions
                           if permission.endswith(":*")])
            return [permission for permission in permissions
                    if (permission.endswith(":*") or
                        permission.split(":")[0] not in wildcards)]
        return wrapped
    
    @wildcard_override
    def role_permissions(self, endpoint,
                         defaults = ["logs:CreateLogGroup",
                                     "logs:CreateLogStream",
                                     "logs:PutLogEvents"]):
        permissions = set(defaults)
        if "permissions" in endpoint:
            permissions.update(set(endpoint["permissions"]))
        return sorted(list(permissions))

    def init_role(self, namespace, endpoint):
        return Role(namespace = namespace,
                    permissions = self.role_permissions(endpoint))
    
    def init_lambda_permission(self, parent_ns, child_ns, endpoint):
        restapiref, stageref = H(f"{parent_ns}-rest-api"), H(f"{parent_ns}-stage")
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{restapiref}}}/${{{stageref}}}/{endpoint['method']}/{endpoint['path']}"}
        return lambda_module.Permission(namespace = child_ns,    
                                        function_namespace = child_ns,
                                        source_arn = source_arn,
                                        principal = "apigateway.amazonaws.com")
        
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

    
