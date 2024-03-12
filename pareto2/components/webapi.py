from pareto2.aws import hungarorise as H

from pareto2.aws.apigateway import *
from pareto2.aws.apigateway import Resource as ApiGatewayResource
from pareto2.aws.cognito import *
from pareto2.aws.iam import Role as RoleBase
from pareto2.aws.route53 import *

# from pareto2.aws.lambda import Permission as PermissionBase

import importlib
lambda_module = importlib.import_module("pareto2.aws.lambda")
PermissionBase = lambda_module.Permission

from pareto2.components import Component

import re

class Permission(PermissionBase):
    
    def __init__(self, namespace, parent_namespace, function_namespace, method, path):
        restapiref, stageref = H(f"{parent_namespace}-rest-api"), H(f"{parent_namespace}-stage")
        source_arn = {"Fn::Sub": f"arn:aws:execute-api:${{AWS::Region}}:${{AWS::AccountId}}:${{{restapiref}}}/${{{stageref}}}/{method}/{path}"}
        super().__init__(namespace=namespace,
                         function_namespace=function_namespace,
                         source_arn=source_arn,
                         principal="apigateway.amazonaws.com")

class IdentityPoolRole(RoleBase):

    def __init__(self, namespace, permissions):
        super().__init__(namespace, permissions)
    
    def policy_document(self, typestr):
        condition={"StringEquals": {"cognito-identity.amazonaws.com:aud": {"Ref": H(f"{self.namespace}-identity-pool")}},
                   "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": typestr}}
        statement=[{"Effect": "Allow",
                    "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                    "Action": ["sts:AssumeRoleWithWebIdentity"],
                    "Condition": condition}]
        return {"Version": "2012-10-17",
                "Statement": statement}
        
class IdentityPoolUnauthorizedRole(IdentityPoolRole):

    def __init__(self, namespace):
        super().__init__(namespace=namespace,
                         permissions=["cognito-sync:*"])
        
    @property
    def policy_document(self):
        return IdentityPoolRole.policy_document(self, "unauthorized")
        
class IdentityPoolAuthorizedRole(IdentityPoolRole):

    def __init__(self, namespace):
        super().__init__(namespace=namespace,
                         permissions=["cognito-sync:*",
                                      "cognito-identity:*",
                                      "lambda:InvokeFunction"])
        
    @property
    def policy_document(self):
        return IdentityPoolRole.policy_document(self, "authorized")
        
class WebApi(Component):    

    def __init__(self, namespace, endpoints, auth="public"):
        super().__init__()
        self.auth=auth
        apifn=getattr(self, f"init_{self.auth}_api")
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
                      IdentityPoolUnauthorizedRole,
                      IdentityPoolRoleAttachment]:
            self.append(klass(namespace=namespace))

    def init_api_base(self, namespace):
        for klass in [RestApi,
                      Stage,
                      GatewayResponse4xx,
                      GatewayResponse5xx,
                      DomainName,
                      BasePathMapping,
                      RecordSet]:
            self.append(klass(namespace=namespace))
            
    def endpoint_namespace(self, namespace, endpoint):
        return "%s-%s" % (namespace,
                          "-".join([tok.lower()
                                    for tok in re.split("\\W", endpoint["path"])
                                    if tok != ""]))
    
    def init_endpoint(self, parent_ns, endpoint):
        child_ns = self.endpoint_namespace(parent_ns, endpoint)
        self.append(ApiGatewayResource(namespace=parent_ns, # NB defined in parent_ns not child_ns
                                       path=endpoint["path"]))
        self.append(CorsMethod(namespace=child_ns,
                               parent_namespace=parent_ns,
                               method=endpoint["method"]))
        self.append(Permission(namespace=child_ns,
                               parent_namespace=parent_ns,
                               function_namespace=endpoint["action"],
                               method=endpoint["method"],
                               path=endpoint["path"]))
        if "parameters" in endpoint:
            self.init_GET_endpoint(parent_ns, child_ns, endpoint)
        elif "schema" in endpoint:
            self.init_POST_endpoint(parent_ns, child_ns, endpoint)

    def init_GET_endpoint(self, parent_ns, child_ns, endpoint):
        methodfn=eval(H(f"{self.auth}-lambda-proxy-method"))
        self.append(methodfn(namespace=child_ns,
                             parent_namespace=parent_ns,
                             function_namespace=endpoint["action"],
                             method=endpoint["method"],
                             parameters=endpoint["parameters"]))
        self.append(ParameterRequestValidator(namespace=child_ns,
                                              parent_namespace=parent_ns))

    def init_POST_endpoint(self, parent_ns, child_ns, endpoint):
        methodfn=eval(H(f"{self.auth}-lambda-proxy-method"))
        self.append(methodfn(namespace=child_ns,
                             parent_namespace=parent_ns,
                             function_namespace=endpoint["action"],
                             method=endpoint["method"],
                             schema=endpoint["schema"]))
        self.append(SchemaRequestValidator(namespace=child_ns,
                                           parent_namespace=parent_ns))
        self.append(Model(namespace=child_ns,
                          parent_namespace=parent_ns,
                          schema=endpoint["schema"]))
                    
    def filter_methods(self, parent_ns, endpoints):
        methods = []
        for endpoint in endpoints:
            child_ns = self.endpoint_namespace(parent_ns, endpoint)
            methods += [H(f"{child_ns}-{self.auth}-lambda-proxy-method"),
                        H(f"{child_ns}-cors-method")]
        return methods
    
    def init_deployment(self, namespace, methods):
        self.append(Deployment(namespace=namespace,
                               methods=methods))
            
if __name__=="__main__":
    pass

    
