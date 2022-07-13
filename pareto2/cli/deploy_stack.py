from pareto2.core.template import Template
from pareto2.core.metadata import Metadata

from botocore.exceptions import ClientError, WaiterError

from pareto2.cli import load_config

import boto3, json, os, sys

def deploy_stack(cf, config, template):
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]]
        return stackname in stacknames
    stackname="%s-%s" % (config["AppName"],
                         config["StageName"])
    action="update" if stack_exists(stackname) else "create"
    fn=getattr(cf, "%s_stack" % action)
    url=template.url(config["ArtifactsBucket"])
    fn(StackName=stackname,
       TemplateURL=url,
       Capabilities=["CAPABILITY_IAM"])
    waiter=cf.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)

if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, template")
        stagename, filename = sys.argv[1:3]
        if not os.path.exists(filename):
            raise RuntimeError("file does not exist")
        template=Template(items=json.loads(open(filename).read()))
        config=load_config()
        """
        print ("deploying stack")
        cf=boto3.client("cloudformation")
        deploy_stack(config=config,
                     template=template,
                     cf=cf)
        """
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except WaiterError as error:
        print ("Error: %s" % str(error))

