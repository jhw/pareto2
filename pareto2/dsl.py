from pareto2.template import Template

from pareto2.components import hungarorise

from importlib import import_module

from datetime import datetime

import os, re, yaml

EndpointJSONSchema="http://json-schema.org/draft-07/schema#"

"""
- would like to dynamically import this stuff, probably based on file paths
- but not confident you'll be able to do that if package is part of a layer (what's the AWS filepath??)
"""

import pareto2.components.action
import pareto2.components.api
import pareto2.components.bucket
import pareto2.components.secret
import pareto2.components.table
import pareto2.components.timer
import pareto2.components.topic
import pareto2.components.userpool

import pareto2.dashboard

def init_components(modules, custompaths):
    for path in custompaths:
        if not (os.path.exists(path) and
                os.path.isdir(path)):
            continue
        for filename in os.listdir(path):
            if ("__init__" in filename or
                "__pycache__" in filename):
                continue
            key=filename.split(".")[0]
            modname="%s.%s" % (path.replace("/", "."), key)
            print ("adding %s -> %s" % (key, modname))
            mod=import_module(modname)
            modules[key]=mod   
    return modules

ComponentModules=init_components({"action": pareto2.components.action,
                                  "api": pareto2.components.api,
                                  "bucket": pareto2.components.bucket,
                                  "secret": pareto2.components.secret,                  
                                  "table": pareto2.components.table,
                                  "timer": pareto2.components.timer,
                                  "topic": pareto2.components.topic,
                                  "userpool": pareto2.components.userpool},
                                 custompaths=["components"])

class Config(dict):

    @classmethod
    def initialise(self, filename="config.yaml"):
        struct=yaml.safe_load(open(filename).read())
        config=Config({"globals": Globals(struct["globals"]),
                       "defaults": Defaults(struct["defaults"]),
                       "layers": Layers(struct["layers"]),
                       "components": Components(struct["components"])})
        config.validate().expand()
        return config
        
    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        params={}
        for attr in ["globals",
                     "defaults",
                     "layers"]:
            params.update(self[attr].parameters)
        return params
                
    def validate(self):
        self["components"].validate()
        return self

    def expand(self):
        self["components"].expand()
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
                       name="main",
                       modules=ComponentModules,
                       timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
        template=Template(name=name,
                          timestamp=timestamp)
        for component in self["components"]:
            mod=modules[component["type"]]
            resourcefn=getattr(mod, "render_resources")
            template.resources.update(resourcefn(component))
            outputfn=getattr(mod, "render_outputs")
            template.outputs.update(outputfn(component))
        return template
    
class Globals(dict):

    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        return {hungarorise(k):v
                for k, v in self.items()}

class Defaults(dict):

    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        return {hungarorise(k):v
                for k, v in self.items()}
        
class Layers(dict):

    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        return {"%sLayerArn" % hungarorise(k):v
                for k, v in self.items()}
        
class Components(list):

    def __init__(self, struct):
        list.__init__(self, struct)

    @property
    def actions(self):
        return [component
                for component in self
                if component["type"]=="action"]

    @property
    def apis(self):
        return [component
                for component in self
                if component["type"]=="api"]

    @property
    def buckets(self):
        return [component
                for component in self
                if component["type"]=="bucket"]

    @property
    def endpoints(self):
        endpoints=[]
        for api in self.apis:
            if "endpoints" in api:
                endpoints+=api["endpoints"]
        return endpoints

    @property
    def events(self):
        events=[]
        for action in self.actions:
            if "events" in action:
                events+=action["events"]
        return events
    
    @property
    def secrets(self):
        return [component
                for component in self
                if component["type"]=="secret"]

    @property
    def tables(self):
        return [component
                for component in self
                if component["type"]=="table"]

    @property
    def timers(self):
        return [component
                for component in self
                if component["type"]=="timer"]

    @property
    def topics(self):
        return [component
                for component in self
                if component["type"]=="topic"]

    @property
    def userpools(self):
        return [component
                for component in self
                if component["type"]=="userpool"]
            
    def validate_component_refs(self, errors):
        def filter_refs(element, refs, attr):
            if isinstance(element, list):
                for subelement in element:
                    filter_refs(subelement, refs, attr)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if key==attr:
                        refs.add(subelement)
                    else:
                        filter_refs(subelement, refs, attr)
        def validate_refs(self, attr, errors):
            names=[item["name"]
                   for item in getattr(self, attr)]
            refs=set()
            filter_refs(self, refs, attr[:-1])
            for ref in refs:
                # print (attr[:-1], ref)
                if ref not in names:
                    errors.append("invalid %s reference [%s]" % (attr[:-1], ref))
        for attr in ["actions",
                     "tables",
                     "buckets"]:
            if attr in self:
                validate_refs(self, attr, errors)

    def validate_action_invocations(self, errors):
        def validate_invoctype(self, attr, invoctype, errors):
            actions={action["name"]:action
                     for action in self.actions}
            for component in getattr(self, attr):
                action=actions[component["action"]]
                if action["invocation-type"]!=invoctype:
                    errors.append("%s component %s must be bound to %s action" % (attr,
                                                                                  component["action"],
                                                                                  invoctype))
        for attr, invoctype in [("endpoints", "sync"),
                                ("timers", "sync"),
                                ("topics", "async")]:
            if attr in self:
                validate_invoctype(self, attr, invoctype, errors)

    def validate_action_events(self, errors):
        if "actions" in self:
            for action in self.actions:
                if "events" in action:
                    for event in action["events"]:
                        if (event["type"]=="s3" and
                            "bucket" not in event):
                            errors.append("%s/%s event is missing bucket attr" % (action["name"],
                                                                                  event["name"]))
                        elif (event["type"]=="dynamodb" and
                              "table" not in event):
                            errors.append("%s/%s event is missing table attr" % (action["name"],
                                                                                 event["name"]))

    def validate(self):
        errors=[]
        self.validate_component_refs(errors)
        self.validate_action_invocations(errors)
        self.validate_action_events(errors)
        if errors!=[]:
            raise RuntimeError(", ".join(errors))
        return self

    def expand_action_env_vars(self):
        def expand(action):
            path="%s/index.py" % action["name"].replace("-", "/")
            if not os.path.isfile(path):
                raise RuntimeError("%s handler not found" % action["name"])
            text=open(path).read()
            return [tok[1:-1].lower().replace("_", "-")
                    for tok in re.findall(r"\[(.*?)\]",
                                          re.sub("\\s", "", text))
                    if (tok.upper()==tok and
                        len(tok) > 3)]
        for action in self.actions:
            variables=expand(action)
            """
            if variables!=[]:
                print ("%s -> %s" % (action["name"],
                                     ", ".join(variables)))
            """
            action["env"]={"variables": variables}

    def expand(self):
        self.expand_action_env_vars()
        return self

if __name__=="__main__":
    try:
        config=Config.initialise()
        config.validate().expand()
        print (config)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
