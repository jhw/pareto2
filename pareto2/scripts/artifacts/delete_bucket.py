from botocore.exceptions import ClientError

import boto3
import os

def empty_bucket(fn):
    def wrapped(s3, bucketname):
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket = bucketname)
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    print (obj["Key"])
                    s3.delete_object(Bucket = bucketname,
                                     Key = obj["Key"])
        fn(s3, bucketname)
    return wrapped

@empty_bucket
def delete_bucket(s3, bucketname):
    print (s3.delete_bucket(Bucket = bucketname))
    
if __name__ == "__main__":
    try:
        bucketname = os.environ["ARTIFACTS_BUCKET"]
        if bucketname in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        s3 = boto3.client("s3")
        delete_bucket(s3, bucketname)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
