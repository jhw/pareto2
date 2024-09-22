from botocore.exceptions import ClientError

import boto3
import os

def fetch_resources(cf, stack_name, filter_fn = lambda x: True):
    resources, token = [], None
    while True:
        kwargs = {"StackName": stack_name}
        if token:
            kwargs["NextToken"] = token
        resp = cf.list_stack_resources(**kwargs)
        for resource in resp["StackResourceSummaries"]:
            if filter_fn(resource):
                resources.append(resource)
        if "NextToken" in resp:
            token = resp["NextToken"]
        else:
            break
    return sorted(resources,
                  key = lambda x: x["LastUpdatedTimestamp"])

def empty_bucket(s3, bucketname):
    try:
        print("emptying %s" % bucketname)
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket = bucketname)
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    print("deleting %s" % obj["Key"])
                    s3.delete_object(Bucket = bucketname,
                                     Key = obj["Key"])
    except ClientError as error:
        if error.response["Error"]["Code"] not in ["NoSuchBucket"]:
            raise error

def delete_stack(cf, s3, stack_name):
    print("deleting stack %s" % stack_name)
    filter_fn = lambda x: x["ResourceType"] == "AWS::S3::Bucket"
    buckets = fetch_resources(cf, stack_name, filter_fn)
    for bucket in buckets:
        empty_bucket(s3, bucket["PhysicalResourceId"])
    cf.delete_stack(StackName = stack_name)
    waiter = cf.get_waiter("stack_delete_complete")
    waiter.wait(StackName = stack_name)

if __name__ == "__main__":
    try:
        stack_name = os.environ["APP_NAME"]
        if stack_name in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        cf, s3 = boto3.client("cloudformation"), boto3.client("s3")
        delete_stack(cf, s3, stack_name)
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
