from botocore.exceptions import ClientError, WaiterError

import boto3
import os
import sys

TemplatePath = "https://s3.%s.amazonaws.com/%s/%s"

def stack_exists(cf, stack_name):
    stack_names = [stack["StackName"]
                  for stack in cf.describe_stacks()["Stacks"]]
    return stack_name in stack_names

if __name__ == "__main__":
    try:
        stack_name = os.environ["APP_NAME"]
        if stack_name in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        bucket_name = os.environ["ARTIFACTS_BUCKET"]
        if bucket_name in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        region = os.environ["AWS_REGION"]
        if region in ["", None]:
            raise RuntimeError("AWS_REGION does not exist")
        file_name = "template-latest.json" if len(sys.argv) < 2 else sys.argv[1]
        cf = boto3.client("cloudformation")
        action = "update" if stack_exists(cf, stack_name) else "create"
        fn = getattr(cf, "%s_stack" % action)
        templateurl = TemplatePath % (region,
                                      bucket_name,
                                      file_name)
        fn(StackName = stack_name,
           TemplateURL = templateurl,
           Capabilities = ["CAPABILITY_IAM"])
        waiter = cf.get_waiter("stack_%s_complete" % action)
        waiter.wait(StackName = stack_name)
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
    except WaiterError as error:
        print("Error: %s" % str(error))
