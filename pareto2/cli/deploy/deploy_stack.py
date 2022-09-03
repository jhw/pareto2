from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError, WaiterError

import boto3, os, sys

TemplatePath="https://s3.%s.amazonaws.com/%s/%s"

def stack_exists(cf, stackname):
    stacknames=[stack["StackName"]
                for stack in cf.describe_stacks()["Stacks"]]
    return stackname in stacknames

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage, filename?")
        stagename=sys.argv[1]
        filename="template-latest.json" if len(sys.argv) < 3 else sys.argv[2].split("/")[-1]
        config=Config.initialise()
        stackname="%s-%s" % (config["globals"]["app-name"],
                             stagename)
        cf=boto3.client("cloudformation")
        action="update" if stack_exists(cf, stackname) else "create"
        fn=getattr(cf, "%s_stack" % action)
        templateurl=TemplatePath % (os.environ["AWS_REGION"],
                                    config["globals"]["artifacts-bucket"],
                                    filename)
        params=[{"ParameterKey": "StageName",
                 "ParameterValue": stagename}]
        fn(StackName=stackname,
           Parameters=params,
           TemplateURL=templateurl,
           Capabilities=["CAPABILITY_IAM"])
        waiter=cf.get_waiter("stack_%s_complete" % action)
        waiter.wait(StackName=stackname)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except WaiterError as error:
        print ("Error: %s" % str(error))

