"""
- not every event has a ResourceStatusReason
- but when they fail, they tend to do so
"""

import boto3, re

def load_events(cf, stackname, n):
    events, token = [], None
    while True:
        if len(events) > n:
            break
        kwargs={"StackName": stackname}
        if token:
            kwargs["NextToken"]=token
        resp=cf.describe_stack_events(**kwargs)
        events+=resp["StackEvents"]
        if "NextToken" in resp:
            token=resp["NextToken"]
        else:
            break
    return sorted(events,
                  key=lambda x: x["Timestamp"])[-n:]

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, n")
        stagename, n = sys.argv[1:3]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        from pareto2.scripts import load_config
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"],
                             stagename)
        events, count = load_events(cf, stackname, n), 0
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
        
