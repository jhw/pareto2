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

def init_template(md,
                  name="main",
                  timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S"),
                  home="pareto2/cdk/components"):
    template=Template(name=name,
                      timestamp=timestamp)
    for filename in os.listdir(home):
        if ("__init__" in filename or
            "__pycache__" in filename):
            continue
        modname="%s.%s" % (home.replace("/", "."),
                           filename.split(".")[0])
        mod=import_module(modname)
        fn=getattr(mod, "update_template")
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
