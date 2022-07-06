from pareto2.cdk.template import Template

from importlib import import_module

from datetime import datetime

import os, yaml

class Defaults(dict):

    @classmethod
    def initialise(self, stagename):
        filename="config/%s/defaults.yaml" % stagename
        if not os.path.exists(filename):
            raise RuntimeError("%s defaults does not exist" % stagename)
        return Defaults(yaml.safe_load(open(filename).read()))

    def __init__(self, items={}):
        dict.__init__(self, items)

def init_components(home="pareto2/cdk/components"):
    components={}
    for filename in os.listdir(home):
        if ("__init__" in filename or
            "__pycache__" in filename):
            continue
        key=filename.split(".")[0]
        modname="%s.%s" % (home.replace("/", "."), key)
        mod=import_module(modname)
        fn=getattr(mod, "update_template")
        components[key]=fn
    return components
        
def init_template(md,
                  name="main",
                  timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
    template=Template(name=name,
                      timestamp=timestamp)
    components=init_components()
    for key, fn in components.items():
        fn(template=template,
           md=md)
    defaults=Defaults.initialise(md.stagename)
    template.autofill_parameters(defaults)
    return template

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate()
        template=init_template(md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
