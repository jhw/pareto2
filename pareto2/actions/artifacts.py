from pareto2.core import init_template
from pareto2.core.lambdas import Lambdas
from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.cli import hungarorise, load_config

import boto3, logging, os

from datetime import datetime

logger=logging.getLogger()
logger.setLevel(logging.INFO)

class Artifacts:

    def __init__(self, config, md, timestamp, s3):
        self.config=config
        self.md=md
        self.timestamp=timestamp
        self.s3=s3

    def build_lambdas(self, run_tests):
        lambdas=Lambdas(self.timestamp)
        if run_tests:
            logger.info("running tests")
            lambdas.run_tests()
        lambdas.validate(self.md)
        lambdas.dump_local()
        bucketname=self.config["ArtifactsBucket"]
        lambdas.dump_s3(self.s3, bucketname)
        return lambdas
        
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
        template.parameters.validate()
        template.dump_local()
        template.validate_root()
        template.dump_s3(self.s3, self.config["ArtifactsBucket"])

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
        import sys
        def init_stdout_logger():
            handler=logging.StreamHandler(sys.stdout)
            formatter=logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        init_stdout_logger()
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


