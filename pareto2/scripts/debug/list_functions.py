from botocore.exceptions import ClientError

import boto3, os

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

if __name__ == "__main__":
    try:
        if "APP_NAME" not in os.environ:
            raise RuntimeError("APP_NAME not found")
        stack_name = os.environ["APP_NAME"]
        cf = boto3.client("cloudformation")
        functions = fetch_functions(cf, stack_name)
        for logical_id in sorted(functions.keys()):
            print ("%s\t%s" % (logical_id,
                               functions[logical_id]))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
