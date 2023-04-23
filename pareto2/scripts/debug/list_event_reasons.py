"""
- not every event has a ResourceStatusReason
- but when they fail, they tend to do so
"""

from pareto2.scripts.debug import *

from botocore.exceptions import ClientError

import boto3, os, re, sys

if __name__=="__main__":
    try:
        stackname=os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter n")
        n=sys.argv[1]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        cf=boto3.client("cloudformation")
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
        
