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

def fetch_events(cf, stackname, n, filterfn=lambda x: True):
    events, token = [], None
    while True:
        if len(events) > n:
            break
        kwargs={"StackName": stackname}
        if token:
            kwargs["NextToken"]=token
        resp=cf.describe_stack_events(**kwargs)
        for event in resp["StackEvents"]:
            if filterfn(event):
                events.append(event)
        if "NextToken" in resp:
            token=resp["NextToken"]
        else:
            break
    return sorted(events,
                  key=lambda x: x["Timestamp"])[-n:]

if __name__=="__main__":
    try:
        stackname=os.environ["PKG_ROOT"]
        if stackname in ["", None]:
            raise RuntimeError("PKG_ROOT not found")
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

        
