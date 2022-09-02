import re

def hungarorise(text):
    def format_token(text, abbrevs=[]):
        return text.upper() if text in abbrevs else text.capitalize()
    return "".join([format_token(tok)
                    for tok in text.split("-")])

def load_config(filename="config/app.props"):
    return dict([tok.split("=")
                for tok in open(filename).read().split("\n")
                 if re.sub("\\s", "", tok)!=''])

def fetch_outputs(cf, stackname):
    outputs={}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]]=output["OutputValue"]
    return outputs

