"""
- not every event has a ResourceStatusReason
- but when they fail, they tend to do so
"""

from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, re, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, n")
        stagename, n = sys.argv[1:3]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["app-name"],
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
        
