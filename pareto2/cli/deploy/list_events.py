import boto3, re

def fetch_events(cf, stackname, n):
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

def matches(values, pat):
    for value in values:
        if re.search(pat, str(value)):
            return True
    return False

def format_value(value, n=32):
    text=str(value)
    return text[:n] if len(text) > n else text+"".join([" " for i in range(n-len(text))])

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 4:
            raise RuntimeError("please enter stage, pattern, n")
        stagename, pattern, n = sys.argv[1:4]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n=int(n)
        from pareto2.cli import load_config
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"],
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
        
