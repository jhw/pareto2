import boto3, json

FunctionName, RoleName = "my-function", "my-role"

PolicyDocument={"Version": "2012-10-17",
                "Statement": [{"Effect": "Allow",
                               "Principal": {"Service": "greengrass.amazonaws.com"},
                               "Action": "sts:AssumeRole"}]}

class Pareto2LambdaTestMixin:

    def setup_lambda(self,
                     funcname=FunctionName,
                     rolename=RoleName,
                     policydoc=PolicyDocument):
        self.iam, self.L = boto3.client("iam"), boto3.client("lambda")
        self.funcrole=self.iam.create_role(RoleName=rolename,
                                           AssumeRolePolicyDocument=json.dumps(policydoc))["Role"]
        self.function=self.L.create_function(FunctionName=funcname,
                                             Role=self.funcrole["Arn"],
                                             Code={"ZipFile": "def handler(event, context):\n  print(\"event\")"})
                
    def teardown_lambda(self):
        self.L.delete_function(FunctionName=self.function["FunctionName"])
        self.iam.delete_role(RoleName=self.funcrole["RoleName"])

if __name__=="___main__":
    pass
