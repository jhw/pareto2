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
        if len(sys.argv) < 5:
            raise RuntimeError("Please enter stackname, namespace, email, password")
        stackname, namespace, email, password = sys.argv[1:5]
        if not re.match(EmailRegex, email):
            raise RuntimeError("Invalid email format")
        
        cf = boto3.client("cloudformation")
        outputs = fetch_outputs(cf, stackname)
        
        userpoolkey = hungarorise(f"{namespace}-user-pool")
        if userpoolkey not in outputs:
            raise RuntimeError("Userpool not found")
        
        userpool = outputs[userpoolkey]
        clientkey = hungarorise(f"{namespace}-user-pool-client")
        if clientkey not in outputs:
            raise RuntimeError("Client not found")
        
        client = outputs[clientkey]
        cognito = boto3.client("cognito-idp")
        
        # Create user and suppress email
        response = cognito.admin_create_user(
            UserPoolId=userpool,
            Username=email,
            TemporaryPassword=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            MessageAction='SUPPRESS'
        )
        print(response)
        
        # Set the user password
        response = cognito.admin_set_user_password(
            UserPoolId=userpool,
            Username=email,
            Password=password,
            Permanent=True
        )
        print(response)
    
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ClientError as error:
        print("Error: %s" % str(error))
