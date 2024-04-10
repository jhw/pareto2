from botocore.exceptions import ClientError

import boto3, os, re, sys

def matches(values, pat):
    for value in values:
        if re.search(pat, str(value)):
            return True
    return False

def format_value(value, n=32):
    text=str(value)
    return text[:n] if len(text) > n else text+"".join([" " for i in range(n-len(text))])

def fetch_resources(cf, stackname, filterfn=lambda x: True):
    resources, token = [], None
    while True:
        kwargs={"StackName": stackname}
        if token:
            kwargs["NextToken"]=token
        resp=cf.list_stack_resources(**kwargs)
        for resource in resp["StackResourceSummaries"]:
            if filterfn(resource):
                resources.append(resource)
        if "NextToken" in resp:
            token=resp["NextToken"]
        else:
            break
    return sorted(resources,
                  key=lambda x: x["LastUpdatedTimestamp"])

if __name__=="__main__":
    try:
        stackname=os.environ["PKG_ROOT"]
        if stackname in ["", None]:
            raise RuntimeError("PKG_ROOT not found")
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

