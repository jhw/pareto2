from pareto2.services import hungarorise as H

from pareto2.services.codebuild import *
from pareto2.services.iam import *
from pareto2.services.s3 import *

from pareto2.recipes import Recipe

class PipBuilder(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(S3Project(namespace = namespace,
                              build_spec = open("/".join(__file__.split("/")[:-1]+["build_spec.yaml"])).read()))
        self.append(Bucket(namespace = namespace))
        self.append(Role(namespace = namespace,
                         principal = "codebuild.amazonaws.com"))
        self.append(Policy(namespace = namespace,
                           permissions =["events:PutEvents",
                                         "logs:CreateLogGroup",
                                         "logs:CreateLogStream",
                                         "logs:PutLogEvents",
                                         "codebuild:*",
                                         "s3:PutObject"]))
        
if __name__ == "__main__":
    pass

    
