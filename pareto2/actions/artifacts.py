from pareto2.core import init_template
from pareto2.core.lambdas import Lambdas
from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.cli import hungarorise, load_config

import boto3, os

from datetime import datetime

class Artifacts:

    def __init__(self, config, md, timestamp, s3):
        self.config=config
        self.md=md
        self.timestamp=timestamp
        self.s3=s3

    def build_lambdas(self, run_tests):
        lambdas=Lambdas(self.timestamp)
        if run_tests:
            lambdas.run_tests()
        lambdas.validate(self.md)
        lambdas.dump_local()
        bucketname=self.config["ArtifactsBucket"]
        lambdas.dump_s3(self.s3, bucketname)
        return lambdas
        
    """
    - layer stuff here is temporary and should be replaced by dedicated layer management stack
    """
        
    def init_template_defaults(self, config, md, lambdas):
        defaults=dict(config)
        defaults.update({"ArtifactsKey": lambdas.s3_key})
        layerparams={hungarorise("layer-key-%s" % pkgname): "layer-%s.zip" % pkgname
                     for pkgname in md.actions.packages}
        defaults.update(layerparams)
        return defaults

    @property
    def is_codebuild(self):
        return "CODEBUILD_BUILD_ID" in os.environ
            
    def build_template(self,
                       paths,
                       lambdas,
                       templatename="main"):
        template=init_template(md,
                               paths=paths,
                               name=templatename,
                               timestamp=self.timestamp)
        defaults=self.init_template_defaults(self.config,
                                             self.md,
                                             lambdas)
        template.parameters.update_defaults(defaults)
        template.parameters.validate()
        if not self.is_codebuild:
            template.dump_local()
        else:
            template.dump_codebuild()
        template.validate_root()
        if not self.is_codebuild:
            template.dump_s3(self.s3, self.config["ArtifactsBucket"])

    def build(self,
              component_paths=["pareto2/core/components"],
              run_tests=True):
        lambdas=self.build_lambdas(run_tests)
        self.build_template(paths=component_paths,
                            lambdas=lambdas)
        
if __name__=="__main__":
    try:
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        config=load_config()
        md=Metadata.initialise()
        md.validate().expand()
        s3=boto3.client("s3")
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        artifacts=Artifacts(config=config,
                            md=md,
                            timestamp=timestamp,
                            s3=s3)
        artifacts.build()
    except RuntimeError as error:
        print ("Error: %s" % str(error))


