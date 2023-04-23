from botocore.exceptions import ClientError

import boto3, os, yaml

def fetch_builds(cb, appname):
    projectname="%s-layers" % appname
    resp=cb.list_builds_for_project(projectName=projectname)
    if ("ids" not in resp or
        resp["ids"]==[]):
        raise RuntimeError("no build ids found")
    return cb.batch_get_builds(ids=resp["ids"])["builds"]

if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        cb=boto3.client("codebuild")
        builds=fetch_builds(cb, appname)
        for build in builds:
            print (yaml.safe_dump(build,
                                  default_flow_style=False))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))

