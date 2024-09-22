from botocore.exceptions import ClientError

import boto3
import os

def empty_bucket(fn):
    def wrapped(s3, bucket_name):
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket = bucket_name)
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    print(obj["Key"])
                    s3.delete_object(Bucket = bucket_name,
                                     Key = obj["Key"])
        fn(s3, bucket_name)
    return wrapped

@empty_bucket
def delete_bucket(s3, bucket_name):
    # print(s3.delete_bucket(Bucket = bucket_name))
    pass
    
if __name__ == "__main__":
    try:
        bucket_name = os.environ["ARTIFACTS_BUCKET"]
        if bucket_name in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        s3 = boto3.client("s3")
        delete_bucket(s3, bucket_name)
    except RuntimeError as error:
        print(f"Error: {error}")
    except ClientError as error:
        print(f"Error: {error}")
