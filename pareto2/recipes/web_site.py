from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.apigateway import *
from pareto2.ingredients.apigateway.s3 import *
from pareto2.ingredients.route53 import *
from pareto2.ingredients.s3 import *

from pareto2.recipes import Recipe

class WebSite(Recipe):    

    def __init__(self, namespace):
        super().__init__()
        for klass in [RestApi,
                      Stage,
                      S3Resource,
                      S3ProxyMethod,
                      S3ProxyRole,
                      S3RedirectMethod,
                      DomainName,
                      BasePathMapping,
                      RecordSet,                      
                      StreamingBucket]:
            self.append(klass(namespace = namespace))
        for fn in [self.init_deployment]:
            self.append(fn(namespace))

    def init_deployment(self, namespace):        
        method_refs = [H(f"{namespace}-s3-proxy-method"),
                       H(f"{namespace}-s3-redirect-method")]
        return Deployment(namespace = namespace,
                          methods = method_refs)
            
if __name__ == "__main__":
    pass

    
