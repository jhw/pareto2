from botocore.exceptions import ClientError

import boto3
import os
import sys

if __name__ == "__main__":
    try:
        bucket_name = os.environ["ARTIFACTS_BUCKET"]
        if bucket_name in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter object key")
        key = sys.argv[1]
        s3 = boto3.client("s3")        
        resp = s3.get_object(Bucket = bucket_name,
                             Key = key)
        with open("tmp/%s" % key.replace("/", "-"), 'wb') as f:
            f.write(resp["Body"].read())
    except RuntimeError as error:
        print(f"Error: {error}")
    except ClientError as error:
        print(f"Error: {error}")
