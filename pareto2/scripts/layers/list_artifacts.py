from botocore.exceptions import ClientError

import boto3, os

"""
- okay to create an in- memory list here as there shouldn't be too many, due to layer prefix
"""

def fetch_artifacts(s3, bucketname, prefix="layer"):
    paginator=s3.get_paginator("list_objects_v2")
    kwargs={"Bucket": bucketname,
            "Prefix": prefix}
    pages=paginator.paginate(**kwargs)
    objects=[]
    for struct in pages:
        if "Contents" in struct:
            objects+=struct["Contents"]
    return objects
    
if __name__=="__main__":
    try:
        bucketname=os.environ["ARTIFACTS_BUCKET"]
        if bucketname in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        s3=boto3.client("s3")
        artifacts=fetch_artifacts(s3, bucketname)
        for obj in artifacts:
            print ("%s\t%s\t%s" % (obj["LastModified"],
                                   obj["Size"],
                                   obj["Key"]))
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
