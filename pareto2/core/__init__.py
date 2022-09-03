from pareto2.core.template import Template

from importlib import import_module

from datetime import datetime

import os

"""
- this is probably not going to work inside a layer as file paths there look different
"""
        
def init_component_renderers(paths):
    components={}
    for path in paths:
        if not (os.path.exists(path) and
                os.path.isdir(path)):
            continue
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
        
def init_template(components,                  
                  name="main",
                  paths=["pareto2/core/components"],
                  timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
    template=Template(name=name,
                      timestamp=timestamp)
    renderers=init_component_renderers(paths)
    for key, renderfn in renderers.items():
        renderfn(template=template,
                 components=components)
    return template

if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        template=init_template(config["components"])
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
