from botocore.exceptions import ClientError, WaiterError

import boto3, os, sys

TemplatePath = "https://s3.%s.amazonaws.com/%s/%s"

def stack_exists(cf, stackname):
    stacknames = [stack["StackName"]
                  for stack in cf.describe_stacks()["Stacks"]]
    return stackname in stacknames

if __name__ == "__main__":
    try:
        stackname = os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        bucketname = os.environ["ARTIFACTS_BUCKET"]
        if bucketname in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        region = os.environ["AWS_REGION"]
        if region in ["", None]:
            raise RuntimeError("AWS_REGION does not exist")
        filename = "template-latest.json" if len(sys.argv) < 2 else sys.argv[1]
        cf = boto3.client("cloudformation")
        action = "update" if stack_exists(cf, stackname) else "create"
        fn = getattr(cf, "%s_stack" % action)
        templateurl = TemplatePath % (region,
                                      bucketname,
                                      filename)
        fn(StackName = stackname,
           TemplateURL = templateurl,
           Capabilities = ["CAPABILITY_IAM"])
        waiter = cf.get_waiter("stack_%s_complete" % action)
        waiter.wait(StackName = stackname)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except WaiterError as error:
        print ("Error: %s" % str(error))
