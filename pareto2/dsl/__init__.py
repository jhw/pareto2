from pareto2.dsl.components import Components

from pareto2.dsl.scripts import Scripts, Script

from pareto2.template import Template

from pareto2.components import hungarorise

import importlib, json, os, yaml

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

    def import_component_module(self,
                                component,
                                paths=["pareto2.components.%s",
                                       "ext.%s"]):
        for path in paths:
            try:
                return importlib.import_module("pareto2.components.%s" % component["type"])
            except ModuleNotFoundError:
                pass
        raise RuntimeError("couldn't import module for component %s" % component["type"])

    """
    - no need for a module cache here as Python/importlib will check sys.modules
    """
    
    def spawn_template(self):
        template=Template()
        for component in self["components"]:
            mod=self.import_component_module(component)
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
        def sort_nested_json(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    obj[key] = sort_nested_json(value)
            elif isinstance(obj, list):
                if all(isinstance(item, dict) and 'name' in item for item in obj):
                    obj.sort(key=lambda x: x['name'])
                elif all(isinstance(item, str) for item in obj):
                    obj.sort()
                else:
                    raise RuntimeError("list contains unsupported types or is missing 'name' field in dicts")
            return obj
        struct=sort_nested_json(self)
        return json.dumps(struct,
                          sort_keys=True,
                          indent=2)
    

if __name__=="__main__":    
    try:
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
