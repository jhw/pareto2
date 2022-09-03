from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, sys

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
        prefix=sys.argv[1] if len(sys.argv) > 1 else None            
        config=Config.initialise()
        bucketname=config["globals"]["artifacts-bucket"]
        s3=boto3.client("s3")
        list_contents(s3, bucketname, prefix)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
