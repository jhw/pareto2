from botocore.exceptions import ClientError

import boto3, yaml

def list_builds(cb, config):
    projectname="%s-layers" % config["AppName"]
    resp=cb.list_builds_for_project(projectName=projectname)
    if ("ids" not in resp or
        resp["ids"]==[]):
        raise RuntimeError("no build ids found")
    builds=cb.batch_get_builds(ids=resp["ids"])["builds"]
    for build in builds:
        print (yaml.safe_dump(build,
                              default_flow_style=False))
    
if __name__=="__main__":
    try:
        from scripts.helpers import load_config
        config=load_config()
        cb=boto3.client("codebuild")
        list_builds(cb, config)
    except ClientError as error:
        print ("Error: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))

