from botocore.exceptions import ClientError

import boto3, os, re

def format_value(value, n = 32):
    text = str(value)
    return text[:n] if len(text) > n else text+"".join([" " for i in range(n-len(text))])

def fetch_resources(cf, stackname):
    resources, token = [], None
    while True:
        kwargs = {"StackName": stackname}
        if token:
            kwargs["NextToken"] = token
        resp = cf.list_stack_resources(**kwargs)
        for resource in resp["StackResourceSummaries"]:
            resources.append(resource)
        if "NextToken" in resp:
            token = resp["NextToken"]
        else:
            break
    return sorted(resources,
                  key = lambda x: x["LastUpdatedTimestamp"])

if __name__ == "__main__":
    try:
        stackname = os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        cf = boto3.client("cloudformation")
        resources, count = fetch_resources(cf, stackname), 0
        for resource in resources:
            values = [resource[attr] if attr in resource else ""
                    for attr in ["LastUpdatedTimestamp",
                                 "LogicalResourceId",
                                 "PhysicalResourceId",
                                 "ResourceType",
                                 "ResourceStatus"]]
            formatstr = " ".join(["%s" for value in values])
            print (formatstr % tuple([format_value(value)
                                      for value in values]))
            count += 1
        print ()
        print ("%i resources" % count)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

