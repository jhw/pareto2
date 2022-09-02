"""
- not every event has a ResourceStatusReason
- but when they fail, they tend to do so
"""

from pareto2.cli.deploy import *

from botocore.exceptions import ClientError

import boto3, re

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, n")
        stagename, n = sys.argv[1:3]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        from pareto2.cli import load_config
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"],
                             stagename)
        events, count = fetch_events(cf, stackname, n), 0
        for event in events:
            if "ResourceStatusReason" not in event:
                continue
            print ("%s => %s" % (event["LogicalResourceId"],
                                 event["ResourceStatusReason"]))
            count+=1
        print ()
        print ("%i events" % count)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
        
