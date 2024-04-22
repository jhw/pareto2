from pareto2.api import file_loader
from pareto2.api.assets import Assets
from pareto2.api.env import Env
from pareto2.api.templater import Templater

from botocore.exceptions import ClientError

from datetime import datetime

import boto3

if __name__=="__main__":
    try:
        s3 = boto3.client("s3")
        env = Env.create_from_environ()
        if "PkgRoot" not in env:
            raise RuntimeError("env is missing PKG_ROOT")
        filter_fn = lambda x: not x.endswith("test.py")
        assets = Assets({k:v for k, v in file_loader(env["PkgRoot"],
                                                     filter_fn = filter_fn)})
        if "ArtifactsBucket" not in env:
            raise RuntimeError("env is missing ARTIFACTS_BUCKET")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        artifacts_key = f"lambdas-{timestamp}.zip"
        assets.dump_s3(s3 = s3,
                       bucket_name = env["ArtifactsBucket"],
                       key = artifacts_key)
        env.update_layers()
        env.update_certificates()
        env["ArtifactsBucket"] = env["ArtifactsBucket"]
        env["ArtifactsKey"] = artifacts_key
        templater = Templater(pkg_root = env["PkgRoot"],
                              assets = assets)
        template = templater.spawn_template(env = env)
        if not template.is_complete:
            raise RuntimeError("template missing parameters %s" % ", ".join(template.unpopulated_parameters))
        for key in [f"template-{timestamp}.json",
                    "template-latest.json"]:
            template.dump_s3(s3 = s3,
                             bucket_name = bucket_name,
                             key = key)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
