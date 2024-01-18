from pareto2.dsl.components import Components

from pareto2.dsl.scripts import Scripts, Script

from pareto2.template import Template

from pareto2.components import hungarorise

import pareto2.components.action
import pareto2.components.api
import pareto2.components.bucket
import pareto2.components.logs
import pareto2.components.queue
import pareto2.components.table
import pareto2.components.timer
import pareto2.components.topic
import pareto2.components.user
import pareto2.components.website

import json, os, yaml

ComponentModules={"action": pareto2.components.action,
                  "api": pareto2.components.api,
                  "bucket": pareto2.components.bucket,
                  "logs": pareto2.components.logs,
                  "queue": pareto2.components.queue,
                  "table": pareto2.components.table,
                  "timer": pareto2.components.timer,
                  "topic": pareto2.components.topic,
                  "user": pareto2.components.user,
                  "website": pareto2.components.website}

ParameterDefaults=yaml.safe_load("""
memory-size-default: 512
memory-size-large: 2048
memory-size-medium: 1024
runtime-version: '3.10'
timeout-default: 5
timeout-long: 30
timeout-medium: 15
""")

LogsDSL=yaml.safe_load("""
- name: warn
  level: warning
  type: logs
  function:
    size: default
    timeout: default
- name: error
  level: error
  type: logs
  function:
    size: default
    timeout: default
""")

class Parameters(dict):

    def __init__(self, struct={}):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        return {hungarorise(k):v
                for k, v in self.items()}

class DSL(dict):

    def __init__(self,
                 parameters=ParameterDefaults,
                 components=[]):
        dict.__init__(self,
                      {"parameters": Parameters(parameters),
                       "components": Components(components)})
        
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

    def assert_singleton(type):
        def decorator(fn):
            def wrapped(self, *args, **kwargs):
                struct=fn(self, *args, **kwargs)
                components=[component for component in struct["components"]
                            if component["type"]==type]
                if len(components) > 1:
                    names=[component["name"] for component in components]
                    raise RuntimeError("multiple %ss are defined [%s]" % (type, ", ".join(names)))
                return struct
            return wrapped
        return decorator

    def assert_bucket_website(fn):
        def wrapped(self, *args, **kwargs):
            struct=fn(self, *args, **kwargs)
            buckets=[component for component in struct["components"]
                     if component["type"]=="bucket"]
            websites=[component for component in struct["components"]
                      if component["type"]=="website"]
            if buckets!=[] and websites!=[]:
                raise RuntimeError("can't define both bucket and website")
            return struct
        return wrapped
    
    @assert_singleton("table")
    @assert_singleton("bucket")
    @assert_singleton("website")
    @assert_singleton("api")
    @assert_bucket_website
    def expand(self,
               scripts,
               globals={},
               logs=LogsDSL):
        self["parameters"].update(globals)                
        self["components"]+=logs
        for attr in ["apis",
                     "buckets",
                     "queues",
                     "tables",
                     "timers",
                     "topics",
                     "users",
                     "websites"]:
            self["components"]+=getattr(scripts, attr)
        for script in scripts:
            action, envvars, = script.action, script.envvars
            if envvars!=[]:
                action["env"]={"variables": envvars}
            self["components"].append(action)
        self.attach_endpoints(scripts)
        self.attach_indexes(scripts)
        return self
    
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
    - because expander wants to do DSL diffs and the simplest way is to do simple string comparison
    - dicts will be auto- sorted by json.dumps, but you have to do lists yourself
    - this could probably be done auto- magically
    """    
        
    @property
    def formatted(self):
        def format_component(component):
            if component["type"]=="action":
                for attr in ["events",
                             "indexes"]:
                    if attr in component:
                        component["events"]=sorted(component[attr],
                                                   key=lambda x: x["name"])
                for attr in ["layers",
                             "permissions"]:
                    if attr in component:
                        component[attr]=sorted(component[attr])
            elif component["type"]=="api":
                if "endpoints" in component:
                    for endpoint in component["endpoints"]:
                        if "parameters" in endpoint:
                            endpoint["parameters"]=sorted(endpoint["parameters"])
            return component
        struct={}
        struct["parameters"]=self["parameters"]
        struct["components"]=sorted([format_component(component)
                                     for component in self["components"]],
                                    key=lambda x: "%s-%s" % (x["type"],
                                                             x["name"]))
        return json.dumps(struct,
                          sort_keys=True,
                          indent=2)
    
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
        dsl=DSL()
        scripts=Scripts.initialise(load_files("demo/hello"))
        dsl.expand(scripts)
        print (dsl.formatted)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        with open("tmp/template.json", 'w') as f:
            f.write(json.dumps(template.render(),                               
                               indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
