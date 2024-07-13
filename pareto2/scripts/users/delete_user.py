from botocore.exceptions import ClientError
import boto3, re, sys

EmailRegex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def hungarorise(text):
    return "".join([tok.capitalize() for tok in re.split("\\-|\\_", text)])

def fetch_outputs(cf, stackname):
    outputs = {}
    for stack in cf.describe_stacks()["Stacks"]:
        if stack["StackName"] == stackname and "Outputs" in stack:
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs

if __name__ == "__main__":
    try:
        if len(sys.argv) < 4:
            raise RuntimeError("Please enter stackname, namespace, email")
        stackname, namespace, email = sys.argv[1:4]
        if not re.match(EmailRegex, email):
            raise RuntimeError("Invalid email format")        
        cf = boto3.client("cloudformation")
        outputs = fetch_outputs(cf, stackname)        
        userpoolkey = hungarorise(f"{namespace}-user-pool")
        if userpoolkey not in outputs:
            raise RuntimeError("Userpool not found")        
        userpool = outputs[userpoolkey]
        cognito = boto3.client("cognito-idp")        
        users_resp = cognito.list_users(
            UserPoolId=userpool,
            Filter=f'email = "{email}"'
        )        
        if not users_resp['Users']:
            raise RuntimeError("No users found with the given email")
        for user in users_resp['Users']:
            username = user['Username']
            delete_resp = cognito.admin_delete_user(
                UserPoolId=userpool,
                Username=username
            )
            print(f"Deleted user {username}: {delete_resp}")    
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
