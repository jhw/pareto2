from botocore.exceptions import ClientError

import boto3
import os
import sys

def list_contents(s3, bucket_name, prefix):
    paginator = s3.get_paginator("list_objects_v2")
    kwargs = {"Bucket": bucket_name}
    if prefix:
        kwargs["Prefix"] = prefix
    pages = paginator.paginate(**kwargs)
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                print("%s\t%s\t%s" % (obj["LastModified"],
                                       obj["Size"],
                                       obj["Key"]))
    
if __name__ == "__main__":
    try:
        bucket_name = os.environ["ARTIFACTS_BUCKET"]
        if bucket_name in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        prefix = sys.argv[1] if len(sys.argv) > 1 else None            
        s3 = boto3.client("s3")
        list_contents(s3, bucket_name, prefix)
    except RuntimeError as error:
        print(f"Error: {error}")
    except ClientError as error:
        print(f"Error: {error}")
