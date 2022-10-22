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
    try:
        from pareto2.dsl import Config
        config=Config.init_file(filename="demo.yaml")
        from pareto2.template import Template
        template=Template()
        for secret in config["components"].secrets:
            template.resources.update(render_resources(secret))
            template.outputs.update(render_outputs(secret))
        print (template.render())
    except RuntimeError as error:
        print ("Error: %s" % str(error))
