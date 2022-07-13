from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.actions.lambdas import Lambdas
from pareto2.actions.layers import Layers
from pareto2.actions.parameters import Parameters

from botocore.exceptions import ClientError, WaiterError

import boto3, yaml

def has_internet():
    import http.client as httplib
    conn=httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except:
        return False

if __name__=="__main__":
    try:
        import os, sys
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter deploy stage")
        stagename=sys.argv[1]
        print ("initialising/validating metadata")
        from datetime import datetime
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        from pareto2.cli import load_config
        config=load_config()
        md=Metadata.initialise(stagename)
        md.validate().expand()
        print ("initialising/validating lambdas")
        lambdas=Lambdas.initialise(md=md,
                                   timestamp=timestamp)
        lambdas.validate()
        lambdas.dump_zip()
        config.update({"StageName": stagename,
                       "ArtifactsKey": lambdas.s3_key_zip})
        print ("initialising/validating layers")
        s3=boto3.client("s3")
        layers=Layers.initialise(md)
        if has_internet():
            layers.validate(s3, config)
        print ("initialising/validating template")
        from pareto2.core import init_template
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        print ()
        print (yaml.safe_dump(template.metrics,
                              default_flow_style=False))
        template.dump_json(template.filename_json)
        template.validate_root()
        params=Parameters.initialise([config,
                                      layers.parameters])
        params.validate(template)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except WaiterError as error:
        print ("Error: %s" % str(error))

