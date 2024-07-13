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
        if len(sys.argv) < 5:
            raise RuntimeError("please enter stackname, namespace, email, password")
        stackname, namespace, email, password = sys.argv[1:5]
        if not re.match(EmailRegex, email):
            raise RuntimeError("invalid email format")
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
        print (cognito.sign_up(ClientId = client,
                               Username = email,
                               Password = password))
        print (cognito.admin_confirm_sign_up(UserPoolId = userpool,
                                             Username = email))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

