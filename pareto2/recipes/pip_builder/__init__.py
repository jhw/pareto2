from pareto2.services import hungarorise as H

from pareto2.services.codebuild import *

from pareto2.recipes import Recipe

class PipBuilder(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(S3Project(namespace = namespace,
                              bucket_namespace = namespace,
                              build_spec = open("/".join(__file__.split("/")[:-1]+["build_spec.yaml"])).read()))

        
if __name__ == "__main__":
    pass

    
