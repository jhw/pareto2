from pareto2.core.metadata import Metadata
from pareto2.core.template import Template
from pareto2.actions.lambdas import Lambdas
from pareto2.actions.layers import Layers

if __name__=="__main__":
    try:
        import os, sys
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter deploy stage")
        stagename=sys.argv[1]
        # initialising/validating metadata
        from datetime import datetime
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        from pareto2.cli import load_config
        config=load_config()
        md=Metadata.initialise(stagename)
        md.validate().expand()
        # initialising/validating lambdas
        lambdas=Lambdas.initialise(md=md,
                                   timestamp=timestamp)
        lambdas.validate()
        lambdas.dump_zip()
        config.update({"StageName": stagename,
                       "ArtifactsKey": lambdas.s3_key_zip})
        # initialising/validating layers
        layers=Layers.initialise(md)
        # initialising/validating template
        from pareto2.core import init_template
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        print ("dumping to %s" % template.filename_json)
        template.dump_json(template.filename_json)
        template.validate_root()
    except RuntimeError as error:
        print ("Error: %s" % str(error))


