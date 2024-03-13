from pareto2.services import hungarorise as H

from pareto2.services.apigateway import *
from pareto2.services.iam import Role as RoleBase
from pareto2.services.route53 import *
from pareto2.services.s3 import *

from pareto2.recipes import Recipe

class Role(RoleBase):

    def __init__(self,
                 namespace,
                 principal = "apigateway.amazonaws.com"):
        bucket_ref = H(f"{namespace}-bucket")
        permissions = [{"action": "s3:GetObject",
                        "resource": {"Fn::Sub": f"arn:aws:s3:::${{{bucket_ref}}}/*"}}]
        super().__init__(namespace,
                         permissions = permissions,
                         principal = principal)

class Website(Recipe):    

    def __init__(self, namespace):
        super().__init__()
        for klass in [RestApi,
                      Stage,
                      S3ProxyResource,
                      S3ProxyMethod,
                      RootRedirectMethod,
                      Role,
                      DomainName,
                      BasePathMapping,
                      RecordSet,                      
                      StreamingBucket]:
            self.append(klass(namespace = namespace))
        method_refs = [H(f"{namespace}-s3-proxy-method"),
                       H(f"{namespace}-root-redirect-method")]
        self.append(Deployment(namespace = namespace,
                               methods = method_refs))
            
if __name__ == "__main__":
    pass

    
