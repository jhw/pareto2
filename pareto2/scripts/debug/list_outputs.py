from pareto2.scripts.debug import *

from botocore.exceptions import ClientError

import boto3, os

if __name__=="__main__":
    try:
        stackname=os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        cf=boto3.client("cloudformation")
        outputs=fetch_outputs(cf, stackname)
        for k in sorted(outputs.keys()):
            print ("%s\t%s" % (format_value(k),
                               outputs[k]))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
        
