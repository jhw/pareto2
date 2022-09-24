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
    def init_file(self, filename="config.yaml"):
        struct=yaml.safe_load(open(filename).read())
        config=Config({"defaults": Defaults(struct["defaults"]),
                       "layers": Layers(struct["layers"]),
                       "components": Components(struct["components"])})
        config.validate()
        return config
        
    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        params={}
        for attr in ["defaults",
                     "layers"]:
            params.update(self[attr].parameters)
        return params

    def validate_layers(self):
        layernames, errors = list(self["layers"].keys()), set()
        for component in self["components"]:
            if (component["type"]=="action" and
                "packages" in component):
                for packagename in component["packages"]:
                    if packagename not in layernames:
                        errors.add(packagename)
        if len(errors) > 0:
            raise RuntimeError("unknown package(s) %s" % ", ".join(errors))
    
    def validate(self):
        self["components"].validate()
        self.validate_layers()
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

    def validate_names(self, errors):
        types=set([item["type"]
                   for item in self])
        for type in types:
            names=[item["name"]
                   for item in self
                   if item["type"]==type]
            if len(names)!=len(set(names)):
                errors.append("%s names are not unique" % type)
    
    def validate_refs(self, errors):
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
            # print (attr, names, refs)
            for ref in refs:
                if ref not in names:
                    errors.append("invalid %s reference [%s]" % (attr[:-1], ref))
        for attr in ["actions",
                     "buckets",
                     "tables",
                     "topics",
                     "userpools"]:
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
            validate_invoctype(self, attr, invoctype, errors)

    def validate_action_events(self, errors):
        def validate_event(action, event, errors):
            for key, attr in [("s3", "bucket"),
                              ("dynamodb", "table"),
                              ("lambda", "action")]:
                if (event["type"]==key and
                    attr not in event):
                    errors.append("%s/%s event is missing %s attr" % (action["name"],
                                                                      event["name"],
                                                                      attr))
        for action in self.actions:
            if "events" in action:
                names=[]
                for event in action["events"]:
                    validate_event(action, event, errors)
                if len(names)!=len(set(names)):
                    errors.append("%s event names are not unique" % action["name"])

    def validate_api_endpoints(self, errors):
        for api in self.apis:
            names, paths = [], []
            for endpoint in api["endpoints"]:
                names.append(endpoint["name"])
                paths.append(endpoint["path"])
            if len(names)!=len(set(names)):
                errors.append("%s endpoint names are not unique" % api["name"])
            if len(paths)!=len(set(paths)):
                errors.append("%s endpoint paths are not unique" % api["name"])
                    
    def validate(self):
        for fn in [self.validate_names,
                   self.validate_refs,
                   self.validate_action_invocations,
                   self.validate_action_events,
                   self.validate_api_endpoints]:
            errors=[]
            fn(errors)
            if errors!=[]:
                raise RuntimeError(", ".join(errors))
        return self

if __name__=="__main__":
    try:
        config=Config.init_file()
        print (config)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
