from pareto2.core.metadata import Metadata

from pareto2.cli import load_config

from botocore.exceptions import ClientError, WaiterError

import boto3, yaml

TemplatePath="https://s3.%s.amazonaws.com/%s/%s"

if __name__=="__main__":
    try:
        import os, sys
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage, filename?")
        stagename=sys.argv[1]
        filename="template-latest.json" if len(sys.argv) < 3 else sys.argv[2].split("/")[-1]
        if not os.path.exists("tmp/%s" % filename):
            raise RuntimeError("%s does not exist" % filename)
        config=load_config()
        md=Metadata.initialise()
        md.validate().expand()
        def stack_exists(cf, stackname):
            stacknames=[stack["StackName"]
                        for stack in cf.describe_stacks()["Stacks"]]
            return stackname in stacknames
        stackname="%s-%s" % (config["AppName"],
                             stagename)
        cf=boto3.client("cloudformation")
        action="update" if stack_exists(cf, stackname) else "create"
        fn=getattr(cf, "%s_stack" % action)
        templateurl=TemplatePath % (os.environ["AWS_REGION"],
                                    config["ArtifactsBucket"],
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

