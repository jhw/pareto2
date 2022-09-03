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

def init_resources(secrets):
    return dict([init_secret(secret)
                 for secret in secrets])

def init_outputs(secrets):
    return {}

if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("secrets")
        template.resources.update(init_resources(config["components"]["secrets"]))
        template.outputs.update(init_outputs(config["components"]["secrets"]))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
