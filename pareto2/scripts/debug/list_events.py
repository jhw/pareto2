from botocore.exceptions import ClientError

import boto3
import os
import re
import sys

def format_value(value, n = 32):
    text = str(value)
    return text[:n] if len(text) > n else text+"".join([" " for i in range(n-len(text))])

def fetch_events(cf, stackname, n):
    events, token = [], None
    while True:
        if len(events) > n:
            break
        kwargs = {"StackName": stackname}
        if token:
            kwargs["NextToken"] = token
        resp = cf.describe_stack_events(**kwargs)
        for event in resp["StackEvents"]:
            events.append(event)
        if "NextToken" in resp:
            token = resp["NextToken"]
        else:
            break
    return sorted(events,
                  key = lambda x: x["Timestamp"])[-n:]

if __name__ == "__main__":
    try:
        stackname = os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter n")        
        n = sys.argv[1]
        if not re.search("^\\d+$", n):
            raise RuntimeError("n is invalid")
        n = int(n)
        cf = boto3.client("cloudformation")
        events, count = fetch_events(cf, stackname, n), 0
        for event in events:
            values = [event[attr] if attr in event else ""
                    for attr in ["Timestamp",
                                 "LogicalResourceId",
                                 "PhysicalResourceId",
                                 "ResourceType",
                                 "ResourceStatus"]]
            format_str = " ".join(["%s" for value in values])
            print(format_str % tuple([format_value(value)
                                       for value in values]))
            count += 1
        print()
        print(f"{count} events")
    except RuntimeError as error:
        print(f"Error: {error}")
    except ClientError as error:
        print(f"Error: {error}")

        
