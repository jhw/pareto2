import re

UserPool="UsersUserpool"

def load_config(filename="config/app.props"):
    return dict([tok.split("=")
                for tok in open(filename).read().split("\n")
                 if re.sub("\\s", "", tok)!=''])

def load_outputs(cf, stackname):
    outputs={}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]]=output["OutputValue"]
    return outputs


