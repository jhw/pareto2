from pareto2.scripts.helpers import hungarorise

import boto3, re, sys, time

"""
- need to iterate through log groups as lambda may have been deployed but corresponding log group may not have been created yet
- then need to check against live functions because you are likely to have loads of old logs groups with same names but different salts
"""

def filter_loggroup(logs, _lambda, stackname, lambdaname):
    def log_group_name(funcname):
        return "/aws/lambda/%s" % funcname
    def fetch_functions(lam, stackname):
        functions, token = [], None
        while True:            
            resp=lam.list_functions(**{"Marker": token} if token else {})
            functions+=[log_group_name(fn["FunctionName"])
                        for fn in resp["Functions"]
                        if fn["FunctionName"].startswith(stackname)]
            if "NextMarker" in resp:
                token=resp["NextMarker"]
            else:
                break
        return functions
    def fetch_groups(logs, stackname):
        prefix=log_group_name(stackname)
        groupnames, token = [], None
        while True:
            resp=logs.describe_log_groups(**{"nextToken": token} if token else {})
            groupnames+=[group["logGroupName"]
                         for group in resp["logGroups"]
                         if group["logGroupName"].startswith(prefix)]
            if "nextToken" in resp:
                token=resp["nextToken"]
            else:
                break
        return groupnames
    def filter_group(groupnames, lambdaname):
        filtered=[groupname
                  for groupname in groupnames
                  if lambdaname in groupname]
        if filtered==[]:
            raise RuntimeError("no log groups found")
        elif len(filtered) > 1:
            raise RuntimeError("multiple log groups found")
        return filtered.pop()
    funcnames=fetch_functions(_lambda, stackname)
    groupnames=[groupname
                for groupname in fetch_groups(logs, stackname)
                if groupname in funcnames]
    return filter_group(groupnames, hungarorise(lambdaname))

def fetch_events(logs, kwargs):
    events, token = [], None
    while True:
        if token:
            kwargs["nextToken"]=token
        resp=logs.filter_log_events(**kwargs)
        events+=resp["events"]
        if "nextToken" in resp:
            token=resp["nextToken"]
        else:
            break
    return sorted(events,
                  key=lambda x: x["timestamp"])

if __name__=="__main__":
    try:
        from pareto2.scripts.helpers import load_config
        config=load_config()
        if len(sys.argv) < 5:
            raise RuntimeError("Please enter stage, lambda, window, query")
        stage, lambdaname, window, query = sys.argv[1:5]
        if not re.search("^\\d+$", window):
            raise RuntimeError("window is invalid")
        window=int(window)
        logs, _lambda = boto3.client("logs"), boto3.client("lambda")
        stackname="%s-%s" % (config["AppName"], stage)
        groupname=filter_loggroup(logs, _lambda,
                                  stackname=stackname,
                                  lambdaname=lambdaname)
        starttime=int(1000*(time.time()-window))
        kwargs={"logGroupName": groupname,
                "startTime": starttime,
                "interleaved": True}
        if query not in ["*", ""]:
            kwargs["filterPattern"]=query
        events=fetch_events(logs, kwargs)
        for event in events:
            msg=re.sub("\\r|\\n", "", event["message"])
            if (msg.startswith("START") or
                msg.startswith("REPORT") or
                msg.startswith("END") or 
                "Found credentials" in msg):
                continue
            print (msg)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
