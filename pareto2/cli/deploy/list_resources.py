from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, pattern")
        stagename, pattern = sys.argv[1:3]
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["app-name"],
                             stagename)
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

