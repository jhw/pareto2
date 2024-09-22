from botocore.exceptions import ClientError
from pareto2.api import file_loader
from pareto2.api.assets import Assets
from pareto2.api.env import Env
from pareto2.api.templater import Templater

import boto3

if __name__=="__main__":
    try:
        s3 = boto3.client("s3")
        env = Env.create_from_environ()
        env.validate()
        env.update_layers()
        env.update_certificates()
        env["ArtifactsKey"] = "whatevs"
        filter_fn = lambda x: not x.endswith("test.py")
        assets = Assets({k:v for k, v in file_loader(env["PkgRoot"],
                                                     filter_fn = filter_fn)})
        templater = Templater(pkg_root = env["PkgRoot"],
                              assets = assets)
        template = templater.spawn_template(env = env,
                                            validate = False) # else exception thrown and you don't get to see the template
        if not template.is_complete:
            raise RuntimeError("template missing parameters %s" % ", ".join(template.unpopulated_parameters))
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
