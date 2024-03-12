from pareto2.services import hungarorise as H

from pareto2.services.apigateway import *
from pareto2.services.iam import Role as RoleBase
from pareto2.services.route53 import *
from pareto2.services.s3 import *

from pareto2.recipes import Recipe

class Website(Recipe):    

    def __init__(self, namespace):
        super().__init__()
        for klass in [RestApi,
                      Stage,
                      S3ProxyResource,
                      S3ProxyMethod,
                      RootRedirectMethod,
                      DomainName,
                      BasePathMapping,
                      RecordSet,                      
                      StreamingBucket]:
            self.append(klass(namespace=namespace))
            
if __name__=="__main__":
    pass

    
