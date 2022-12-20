from pareto2.config.callbacks import Callbacks
from pareto2.config.components import Components
from pareto2.config.parameters import Parameters
from pareto2.config.scripts import Scripts, Script

from pareto2.template import Template

from pareto2.components import hungarorise

import pareto2.components.action
import pareto2.components.api
import pareto2.components.bucket
import pareto2.components.queue
import pareto2.components.secret
import pareto2.components.table
import pareto2.components.timer
import pareto2.components.topic
import pareto2.components.userpool

import pareto2.dashboard

import os, yaml

ComponentModules={"action": pareto2.components.action,
                  "api": pareto2.components.api,
                  "bucket": pareto2.components.bucket,
                  "queue": pareto2.components.queue,
                  "secret": pareto2.components.secret,
                  "table": pareto2.components.table,
                  "timer": pareto2.components.timer,
                  "topic": pareto2.components.topic,
                  "userpool": pareto2.components.userpool}

ParameterDefaults=yaml.safe_load("""
memory-size-default: 512
memory-size-large: 2048
memory-size-medium: 1024
runtime-version: '3.8'
timeout-default: 5
timeout-long: 30
timeout-medium: 15
""")

class Config(dict):

    def __init__(self,
                 parameters=ParameterDefaults,
                 components=[],
                 callbacks=[]):
        dict.__init__(self,
                      {"parameters": Parameters(parameters),
                       "components": Components(components),
                       "callbacks": Callbacks(callbacks)})
        
    @property
    def parameters(self):
        params={}
        for attr in ["parameters"]:
            params.update(self[attr].parameters)
        return params

    """
    - apis are guaranteed to exist
    """
    
    def attach_endpoints(self, scripts):
        apis={api["name"]:api
              for api in self["components"].apis}
        for script in scripts:
            if "endpoint" in script.infra:
                endpoint=script.infra["endpoint"]
                endpoint["action"]=script.action_name
                api=apis[endpoint["api"]]
                api["endpoints"].append(endpoint)

    """
    - tables are not guaranteed to exist
    - note addition of -table suffix during lookup
    """
                
    def attach_indexes(self, scripts):
        tables={"%s-table" % table["name"]:table
                for table in self["components"].tables}
        for script in scripts:
            if "indexes" in script.infra:
                indexes=script.infra["indexes"]
                for index in indexes:
                    tablename="%s-table" % index.pop("table")
                    if tablename not in tables:
                        raise RuntimeError("%s not found" % tablename)
                    table=tables[tablename]
                    table["indexes"].append(index)
                
    def expand(self, scripts, globals={}):
        self["parameters"].update(globals)
        for attr in ["apis",
                     "buckets",
                     "secrets",
                     "tables",
                     "topics",
                     "userpools"]:
            self["components"]+=getattr(scripts, attr)
        for script in scripts:
            action, envvars, = script.action, script.envvars
            if envvars!=[]:
                action["env"]={"variables": envvars}
            self["components"].append(action)
        self.attach_endpoints(scripts)
        self.attach_indexes(scripts)
        self["callbacks"]+=scripts.callbacks
        return self
    
    def add_dashboard(fn):
        def wrapped(self, *args, **kwargs):
            template=fn(self, *args, **kwargs)
            resourcefn=getattr(pareto2.dashboard,
                               "render_resources")
            template.resources.update(resourcefn(self))
            return template
        return wrapped
    
    @add_dashboard
    def spawn_template(self,                  
                       modules=ComponentModules):
        template=Template()
        for component in self["components"]:
            mod=modules[component["type"]]
            resourcefn=getattr(mod, "render_resources")
            template.resources.update(resourcefn(component))
            outputfn=getattr(mod, "render_outputs")
            template.outputs.update(outputfn(component))
        return template

"""
- load_files is separate from scripts as is implementation detail
- important that it can effectively switch directory
- files may be part of s3 or zip archive rather than local file system
- assumes the tail slug of the root path is the name of the python package
"""
    
def load_files(root):
    roottokens, items = root.split("/"), []
    for localroot, dirs, files in os.walk(root):
        for _filename in files:
            filename=os.path.join(localroot, _filename)
            body=open(filename).read()
            key="/".join(filename.split("/")[len(roottokens)-1:])
            item=(key, body)
            items.append(item)
    return items

if __name__=="__main__":    
    try:
        config=Config()
        scripts=Scripts.initialise(load_files("demo/hello"))
        config.expand(scripts)
        template=config.spawn_template()
        template.init_implied_parameters()
        print (template.render())
    except RuntimeError as error:
        print ("Error: %s" % str(error))
