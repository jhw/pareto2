from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3

def fetch_resources(cf, stackname, filterfn=lambda x: True):
    resources, token = [], None
    while True:
        kwargs={"StackName": stackname}
        if token:
            kwargs["NextToken"]=token
        resp=cf.list_stack_resources(**kwargs)
        for resource in resp["StackResourceSummaries"]:
            if filterfn(resource):
                resources.append(resource)
        if "NextToken" in resp:
            token=resp["NextToken"]
        else:
            break
    return sorted(resources,
                  key=lambda x: x["LastUpdatedTimestamp"])

def empty_bucket(s3, bucketname):
    try:
        print ("emptying %s" % bucketname)
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=bucketname)
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    print ("deleting %s" % obj["Key"])
                    s3.delete_object(Bucket=bucketname,
                                     Key=obj["Key"])
    except ClientError as error:
        if error.response["Error"]["Code"] not in ["NoSuchBucket"]:
            raise error

def delete_stack(cf, s3, stackname):
    print ("deleting stack %s" % stackname)
    filterfn=lambda x: x["ResourceType"]=="AWS::S3::Bucket"
    buckets=fetch_resources(cf, stackname, filterfn)
    for bucket in buckets:
        empty_bucket(s3, bucket["PhysicalResourceId"])
    cf.delete_stack(StackName=stackname)
    waiter=cf.get_waiter("stack_delete_complete")
    waiter.wait(StackName=stackname)

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stage=sys.argv[1]
        config=Config.initialise()
        stackname="%s-%s" % (config["globals"]["AppName"], stage)
        cf, s3 = boto3.client("cloudformation"), boto3.client("s3")
        delete_stack(cf, s3, stackname)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))


