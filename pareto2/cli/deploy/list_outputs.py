from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stagename=sys.argv[1]
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["app-name"],
                             stagename)
        outputs=fetch_outputs(cf, stackname)
        for k in sorted(outputs.keys()):
            print ("%s\t%s" % (format_value(k),
                               format_value(outputs[k])))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
        
