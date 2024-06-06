from botocore.exceptions import ClientError

import boto3, os, re, sys

def hungarorise(text):
    return "".join([tok.capitalize() for tok in re.split("\\-|\\_", text)])

def fetch_outputs(cf, stackname):
    outputs = {}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs

if __name__ == "__main__":
    try:
        if len(sys.argv) < 4:
            raise RuntimeError("please enter stackname, namespace, email")
        stackname, namespace, email, = sys.argv[1:4]
        cf = boto3.client("cloudformation")
        outputs = fetch_outputs(cf, stackname)
        userpoolkey = hungarorise(f"{namespace}-user-pool")
        if userpoolkey not in outputs:
            raise RuntimeError("userpool not found")
        userpool = outputs[userpoolkey]
        clientkey = hungarorise(f"{namespace}-user-pool-client")
        if clientkey not in outputs:
            raise RuntimeError("client not found")
        client = outputs[clientkey]
        cognito = boto3.client("cognito-idp")        
        resp = cognito.admin_create_user(
            UserPoolId=userpool,
            Username=email,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
            ]
        )
        print (resp)
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
