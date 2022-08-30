from pareto2.core import init_template
from pareto2.core.lambdas import Lambdas
from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.cli import load_config

import boto3, os

from datetime import datetime

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
        bucketname=self.config["ArtifactsBucket"]
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
        defaults=dict(self.config)
        defaults.update({"ArtifactsKey": lambdas.s3_key})
        template.parameters.update_defaults(defaults)
        template.dump_s3(self.s3, self.config["ArtifactsBucket"])
        template.parameters.validate()
        template.validate_root()

    def build(self,
              component_paths=["pareto2/core/components"],
              template_name="template",
              run_tests=True):
        if not os.path.exists("tmp"):
            os.mkdir("tmp")                
        lambdas=self.build_lambdas(run_tests)
        self.build_template(name=template_name,
                            paths=component_paths,
                            lambdas=lambdas)
        
if __name__=="__main__":
    try:
        config=load_config(filename="config/app.props")
        md=Metadata.initialise(filename="config/metadata.yaml")
        md.validate().expand()
        root=os.environ["APP_ROOT"]
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        s3=boto3.client("s3")
        artifacts=Artifacts(config=config,
                            md=md,
                            root=root,
                            timestamp=timestamp,
                            s3=s3)
        artifacts.build()
    except RuntimeError as error:
        print ("Error: %s" % str(error))


