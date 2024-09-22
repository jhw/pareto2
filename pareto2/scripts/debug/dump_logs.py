from botocore.exceptions import ClientError

import boto3
import os
import re
import sys
import time

def fetch_functions(cf, stack_name):
    functions, token = {}, None
    while True:
        kwargs = {"StackName": stack_name}
        if token:
            kwargs["NextToken"] = token
        resp = cf.list_stack_resources(**kwargs)
        for resource in resp["StackResourceSummaries"]:
            if resource["ResourceType"] == "AWS::Lambda::Function":
                functions[resource["LogicalResourceId"]] = resource["PhysicalResourceId"]
        if "NextToken" in resp:
            token = resp["NextToken"]
        else:
            break
    return functions

def fetch_log_events(logs, kwargs):
    events, token = [], None
    while True:
        if token:
            kwargs["nextToken"] = token
        resp = logs.filter_log_events(**kwargs)
        events += resp["events"]
        if "nextToken" in resp:
            token = resp["nextToken"]
        else:
            break
    return sorted(events,
                  key = lambda x: x["timestamp"])

if __name__ == "__main__":
    try:
        if "APP_NAME" not in os.environ:
            raise RuntimeError("APP_NAME not found")
        stack_name = os.environ["APP_NAME"]
        if len(sys.argv) < 3:
            raise RuntimeError("please enter function logical id, window")
        logical_id, window = sys.argv[1:3]
        if not re.search("^\\d+$", window):
            raise RuntimeError("window is invalid")
        window = int(window)
        cf, logs = boto3.client("cloudformation"), boto3.client("logs")
        functions = fetch_functions(cf, stack_name)
        start_time = int(1000*(time.time()-window))
        if logical_id not in functions:
            raise RuntimeError("logical id not found")
        physical_id = functions[logical_id]
        log_group_name = "/aws/lambda/%s" % physical_id
        kwargs = {"logGroupName": log_group_name,
                  "startTime": start_time,
                  "interleaved": True}
        events = fetch_log_events(logs, kwargs)
        for event in events:
            msg = re.sub("\\r|\\n", "", event["message"])
            print(msg)
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
