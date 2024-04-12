from botocore.exceptions import ClientError

import boto3, os, re, sys, time

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
        if len(sys.argv) < 3:
            raise RuntimeError("please enter lambda name, window")
        lambdaname, window = sys.argv[1:3]
        if not re.search("^\\d+$", window):
            raise RuntimeError("window is invalid")
        window=int(window)
        logs=boto3.client("logs")
        starttime=int(1000*(time.time()-window))
        loggroupname="/aws/lambda/%s" % lambdaname
        kwargs={"logGroupName": loggroupname,
                "startTime": starttime,
                "interleaved": True}
        events=fetch_log_events(logs, kwargs)
        for event in events:
            msg=re.sub("\\r|\\n", "", event["message"])
            print (msg)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
