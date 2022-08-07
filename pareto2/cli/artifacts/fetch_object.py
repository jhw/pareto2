from botocore.exceptions import ClientError

from pareto2.cli import *

import boto3

def list_contents(s3, bucketname, prefix):
    paginator=s3.get_paginator("list_objects_v2")
    kwargs={"Bucket": bucketname}
    if prefix:
        kwargs["Prefix"]=prefix
    pages=paginator.paginate(**kwargs)
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                print ("%s\t%s\t%s" % (obj["LastModified"],
                                       obj["Size"],
                                       obj["Key"]))
    
if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter object key")
        key=sys.argv[1]
        config=load_config()
        bucketname=config["ArtifactsBucket"]
        s3=boto3.client("s3")        
        resp=s3.get_object(Bucket=bucketname,
                           Key=key)
        with open("tmp/%s" % key, 'wb') as f:
            f.write(resp["Body"].read())
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
