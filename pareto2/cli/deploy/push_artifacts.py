from pareto2.cli.deploy import *

from pareto2.core.dsl import Config
from pareto2.core.lambdas import Lambdas
from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.core import init_template

from botocore.exceptions import ClientError

import boto3

class Artifacts:

    def __init__(self, config, md, root, timestamp, s3):
        self.config=config
        self.md=md
        self.root=root
        self.timestamp=timestamp
        self.s3=s3

    def build_lambdas(self, run_tests):
        lambdas=Lambdas(self.root, self.timestamp)
        if run_tests:
            lambdas.run_tests() # raises RuntimeError on failure
        lambdas.validate(self.md)
        bucketname=self.config["globals"]["ArtifactsBucket"]
        lambdas.dump_s3(self.s3, bucketname)
        return lambdas

    """
    - NB validation occurs after s3 push so any errors are visible
    """
        
    def build_template(self,
                       name,
                       paths,
                       lambdas):
        template=init_template(self.md,
                               paths=paths,
                               name=name,
                               timestamp=self.timestamp)
        """
        - init_implied_parameters initialises parameter variables
        - parameters.update_defaults adds default values
        """
        template.init_implied_parameters({hungarorise(k):v
                                          for k, v in self.config["defaults"].items()})
        values=dict(self.config["globals"])
        values.update({"ArtifactsKey": lambdas.s3_key})
        if "layers" in config:            
            values.update({"%sLayerArn" % k.capitalize(): v
                           for k, v in config["layers"].items()})
        template.parameters.update_defaults(values)
        template.dump_s3(self.s3, self.config["globals"]["ArtifactsBucket"])
        template.parameters.validate()
        template.validate_root()

    def build(self,
              component_paths=["pareto2/core/components"],
              template_name="template",
              run_tests=True):
        lambdas=self.build_lambdas(run_tests)
        self.build_template(name=template_name,
                            paths=component_paths,
                            lambdas=lambdas)

"""
- ensure PYTHONPATH contains PARETO2_APP_PATH so can load module whose root is PARETO2_APP_NAME
- filepath- based module imports are unlikely to work within a layer :(
"""
        
if __name__=="__main__":
    try:
        import os
        apppath, appname = (os.environ["PARETO2_APP_PATH"] if "PARETO2_APP_PATH" in os.environ else ".",
                            os.environ["PARETO2_APP_NAME"])
        config=Config.initialise()
        md=Metadata(config["components"])
        md.validate().expand()
        from datetime import datetime
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        s3=boto3.client("s3")
        artifacts=Artifacts(config=config,
                            md=md,
                            root=appname,
                            timestamp=timestamp,
                            s3=s3)        
        comppaths=["pareto2/core/components",
                   "components"]
        artifacts.build(component_paths=comppaths)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))


