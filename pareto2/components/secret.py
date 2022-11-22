from pareto2.components import hungarorise as H
from pareto2.components import resource

import json

@resource            
def init_secret(secret):
    resourcename=H("%s-secret" % secret["name"])
    props={"Name": secret["name"],
           "SecretString": json.dumps(secret["values"])}
    return (resourcename, 
            "AWS::SecretsManager::Secret",
            props)

def render_resources(secret):
    resources=[]
    resources+=init_secret(secret)
    return dict(secret)

def render_outputs(secret):
    return {}

if __name__=="__main__":
    pass
