from pareto2.cli.deploy import *

from botocore.exceptions import ClientError

import boto3

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stagename=sys.argv[1]
        from pareto2.cli import load_config
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["AppName"],
                             stagename)
        outputs=fetch_outputs(cf, stackname)
        for k in sorted(outputs.keys()):
            print ("%s\t%s" % (format_value(k),
                               format_value(outputs[k])))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
        
