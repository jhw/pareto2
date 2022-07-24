from pareto2.core.template import Template

from importlib import import_module

from datetime import datetime

import os, yaml

class Defaults(dict):

    @classmethod
    def initialise(self,
                   filename="config/defaults.yaml"):
        if not os.path.exists(filename):
            raise RuntimeError("defaults.yaml does not exist")
        return Defaults(yaml.safe_load(open(filename).read()))

    def __init__(self, items={}):
        dict.__init__(self, items)

def init_components(paths):
    components={}
    for path in paths:
        for filename in os.listdir(path):
            if ("__init__" in filename or
                "__pycache__" in filename):
                continue
            key=filename.split(".")[0]
            modname="%s.%s" % (path.replace("/", "."), key)
            mod=import_module(modname)
            fn=getattr(mod, "update_template")
            components[key]=fn
    return components
        
def init_template(md,
                  name="main",
                  paths=["pareto2/core/components"],
                  timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
    template=Template(name=name,
                      timestamp=timestamp)
    components=init_components(paths)
    for key, fn in components.items():
        fn(template=template,
           md=md)
    defaults=Defaults.initialise()
    template.autofill_parameters(defaults)
    return template

if __name__=="__main__":
    try:
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate()
        template=init_template(md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
