from botocore.exceptions import ClientError

import boto3
import os
import re
import sys

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def fetch_outputs(cf, stack_name):
    outputs = {}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"]==stack_name and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs

if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stack_name, namespace")
        stack_name, namespace = sys.argv[1:3]
        cf = boto3.client("cloudformation")
        outputs = fetch_outputs(cf, stack_name)
        userpool_key = hungarorise(f"{namespace}-user-pool")
        if userpool_key not in outputs:
            raise RuntimeError("userpool not found")
        userpool = outputs[userpool_key]
        cognito = boto3.client("cognito-idp")
        resp = cognito.list_users(UserPoolId = userpool)
        print (resp)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

