from pareto2.scripts.debug import hungarorise

from botocore.exceptions import ClientError

import boto3, re, os, sys, time

"""
- need to iterate through log groups as lambda may have been deployed but corresponding log group may not have been created yet
- then need to check against live functions because you are likely to have loads of old logs groups with same names but different salts
"""

def filter_log_group(logs, L, stackname, lambdaname):
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
    funcnames=fetch_functions(L, stackname)
    groupnames=[groupname
                for groupname in fetch_groups(logs, stackname)
                if groupname in funcnames]
    return filter_group(groupnames, hungarorise(lambdaname))

def fetch_log_events(logs, kwargs):
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
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("app package not found")
        if len(sys.argv) < 4:
            raise RuntimeError("Please enter lambda, window, query")
        lambdaname, window, query = sys.argv[1:4]
        if not re.search("^\\d+$", window):
            raise RuntimeError("window is invalid")
        window=int(window)
        logs, L = boto3.client("logs"), boto3.client("lambda")
        stackname=appname
        groupname=filter_log_group(logs, L,
                                   stackname=stackname,
                                   lambdaname=lambdaname)
        starttime=int(1000*(time.time()-window))
        kwargs={"logGroupName": groupname,
                "startTime": starttime,
                "interleaved": True}
        if query not in ["*", ""]:
            kwargs["filterPattern"]=query
        events=fetch_log_events(logs, kwargs)
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
    except ClientError as error:
        print ("Error: %s" % str(error))
