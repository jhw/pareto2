import re

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

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

def fetch_outputs(cf, stackname):
    outputs={}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]]=output["OutputValue"]
    return outputs

if __name__=="__main__":
    pass