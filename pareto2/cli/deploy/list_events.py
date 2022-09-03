from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, re, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 4:
            raise RuntimeError("please enter stage, pattern, n")
        stagename, pattern, n = sys.argv[1:4]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["AppName"],
                             stagename)
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

        
