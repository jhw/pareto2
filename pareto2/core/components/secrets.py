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

def init_resources(md):
    return dict([init_secret(secret)
                 for secret in md.secrets])

def update_template(template, md):
    template["Resources"].update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.core.template import Template
        template=Template("secrets")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
