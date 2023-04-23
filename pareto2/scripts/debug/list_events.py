from pareto2.scripts.debug import *

from botocore.exceptions import ClientError

import boto3, os, re, sys

if __name__=="__main__":
    try:
        stackname=os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        if len(sys.argv) < 3:
            raise RuntimeError("please enter pattern, n")        
        pattern, n = sys.argv[1:3]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        cf=boto3.client("cloudformation")
        events, count = fetch_events(cf, stackname, n), 0
        for event in events:
            values=[event[attr] if attr in event else ""
                    for attr in ["Timestamp",
                                 "LogicalResourceId",
                                 "PhysicalResourceId",
                                 "ResourceType",
                                 "ResourceStatus"]]
            if (pattern not in ["", "*"] and
                not matches(values, pattern)):
                continue            
            formatstr=" ".join(["%s" for value in values])
            print (formatstr % tuple([format_value(value)
                                      for value in values]))
            count+=1
        print ()
        print ("%i events" % count)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

        
