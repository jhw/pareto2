from botocore.exceptions import ClientError

import boto3, os, re, sys

EmailRegex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def fetch_outputs(cf, stackname):
    outputs = {}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"]==stackname and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs

if __name__ == "__main__":
    try:
        if len(sys.argv) < 4:
            raise RuntimeError("please enter stackname, namespace, email")
        stackname, namespace, email = sys.argv[1:4]
        if not re.match(EmailRegex, email):
            raise RuntimeError("invalid email format")
        cf = boto3.client("cloudformation")
        outputs = fetch_outputs(cf, stackname)
        userpoolkey = hungarorise(f"{namespace}-user-pool")
        if userpoolkey not in outputs:
            raise RuntimeError("userpool not found")
        userpool = outputs[userpoolkey]
        cognito = boto3.client("cognito-idp")
        resp = cognito.admin_delete_user(UserPoolId = userpool,
                                         Username = email)
        print (resp)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

