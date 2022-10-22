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
        import os, sys
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        from pareto2.dsl import Config
        config=Config.init_file(filename=filename)
        from pareto2.template import Template
        template=Template()
        for secret in config["components"].secrets:
            template.resources.update(render_resources(secret))
            template.outputs.update(render_outputs(secret))
        print (template.render())
        print ()
        template.init_implied_parameters()
        for validator in [template.parameters.validate,
                          template.validate]:
            try:
                validator()
            except RuntimeError as error:
                print ("Warning: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
