from pareto2.api.assets import Assets, file_loader
from pareto2.api.env import Env
from pareto2.api.project import Project

from botocore.exceptions import ClientError

from datetime import datetime

import boto3, os

def init_filter(pkg_root):
    def filter_fn(full_path):
        return (full_path == f"{pkg_root}/__init__.py" or
                full_path.endswith("index.py"))
    return filter_fn

if __name__=="__main__":
    try:
        for attr in ["PKG_ROOT",
                     "ARTIFACTS_BUCKET",
                     "AWS_REGION"]:            
            if (attr not in os.environ or
                os.environ[attr] in ["", None]):
                raise RuntimeError(f"{attr} does not exist")
        s3 = boto3.client("s3")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        pkg_root = os.environ["PKG_ROOT"]
        filter_fn = init_filter(pkg_root)
        assets = Assets({k:v for k, v in file_loader(pkg_root,
                                                     filter_fn = filter_fn)})
        bucket_name = os.environ["ARTIFACTS_BUCKET"]
        artifacts_key = f"lambdas-{timestamp}.zip"
        assets.dump_s3(s3 = s3,
                       bucket_name = bucket_name,
                       key = artifacts_key)
        env = Env.create_from_environ()
        env.update_layers()
        env.update_certificates()
        env["ArtifactsBucket"] = bucket_name
        env["ArtifactsKey"] = artifacts_key
        project = Project(pkg_root = pkg_root,
                          assets = assets)
        template = project.spawn_template(env = env)
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
