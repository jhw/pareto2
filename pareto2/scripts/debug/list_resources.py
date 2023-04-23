from pareto2.scripts.debug import *

from botocore.exceptions import ClientError

import boto3, os, sys

if __name__=="__main__":
    try:
        stackname=os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter pattern")
        pattern=sys.argv[1]
        cf=boto3.client("cloudformation")
        resources, count = fetch_resources(cf, stackname), 0
        for resource in resources:
            values=[resource[attr] if attr in resource else ""
                    for attr in ["LastUpdatedTimestamp",
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
        print ("%i resources" % count)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

