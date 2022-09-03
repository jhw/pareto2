from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

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
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("secrets")
        for secret in config["components"]["secrets"]:
            template.resources.update(render_resources(secret))
            template.outputs.update(render_outputs(secret))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
