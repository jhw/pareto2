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

def init_resources(components):
    return dict([init_secret(secret)
                 for secret in components["secrets"]])

def init_outputs(components):
    return {}

def update_template(template, components):
    template.resources.update(init_resources(components))
    template.outputs.update(init_outputs(components))
    
if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("secrets")
        update_template(template, config["components"])
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
