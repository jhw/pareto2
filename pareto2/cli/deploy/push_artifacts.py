from pareto2.cli.deploy import *

from pareto2.core.dsl import Config
from pareto2.core.lambdas import Lambdas
from pareto2.core.template import Template

from botocore.exceptions import ClientError

from datetime import datetime

import boto3, os

class Artifacts:

    def __init__(self, config, root, s3,
                 timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
        self.config=config
        self.root=root
        self.s3=s3
        self.timestamp=timestamp

    def build_lambdas(self, run_tests):
        lambdas=Lambdas(self.root, self.timestamp)
        if run_tests:
            lambdas.run_tests() # raises RuntimeError on failure
        lambdas.validate(self.config["components"])
        bucketname=self.config["globals"]["artifacts-bucket"]
        lambdas.dump_s3(self.s3, bucketname)
        return lambdas

    """
    - NB validation occurs after s3 push so any errors are visible
    """
        
    def build_template(self,
                       name,
                       paths,
                       lambdas):
        template=self.config["components"].spawn_template(paths=paths,
                                                          name=name,
                                                          timestamp=self.timestamp)
        template.init_implied_parameters()
        values=self.config.parameters
        values["ArtifactsKey"]=lambdas.s3_key
        template.parameters.update_defaults(values)
        template.dump_s3(self.s3, self.config["globals"]["artifacts-bucket"])
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

if __name__=="__main__":
    try:
        apppath, appname = (os.environ["PARETO2_APP_PATH"] if "PARETO2_APP_PATH" in os.environ else ".",
                            os.environ["PARETO2_APP_NAME"])
        config=Config.initialise("%s/config.yaml" % apppath)
        s3=boto3.client("s3")
        artifacts=Artifacts(config=config,
                            root=appname,
                            s3=s3)        
        comppaths=["pareto2/core/components",
                   "components"]
        artifacts.build(component_paths=comppaths)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))


