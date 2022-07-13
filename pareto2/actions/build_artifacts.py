from pareto2.core import init_template

from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.actions.lambdas import Lambdas

from datetime import datetime

from pareto2.cli import load_config

import os, sys

if __name__=="__main__":
    try:
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stagename=sys.argv[1]
        # initialising/validating metadata
        config=load_config()
        md=Metadata.initialise(stagename)
        md.validate().expand()
        # initialising/validating lambdas
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        lambdas=Lambdas.initialise(md=md,
                                   timestamp=timestamp)
        lambdas.validate()
        lambdas.dump_zip()
        # initialising/validating template
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        print ("dumping to %s" % template.filename_json)
        template.dump_json(template.filename_json)
        template.validate_root()
    except RuntimeError as error:
        print ("Error: %s" % str(error))


