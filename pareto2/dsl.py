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
        config=Config({"parameters": Parameters(struct["parameters"]),
                       "components": Components(struct["components"])})
        config.validate()
        return config
        
    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        params={}
        for attr in ["parameters"]:
            params.update(self[attr].parameters)
        return params

    def cross_validate_layers(self):
        layernames, errors = self["parameters"].layers.names, set()
        for component in self["components"]:
            if (component["type"]=="action" and
                "layers" in component):
                for layername in component["layers"]:
                    if layername not in layernames:
                        errors.add(layername)
        if len(errors) > 0:
            raise RuntimeError("unknown layer(s) %s" % ", ".join(errors))
        
    def validate(self):
        for attr in ["parameters",
                     "components"]:
            self[attr].validate()
        self.cross_validate_layers()
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

class Layers(dict):

    @classmethod
    def initialise(self, parameters):
        layers={}
        for k, v in parameters.items():
            if (isinstance(v, str) and
                v.startswith("arn:aws:lambda:") and
                ":layer:" in v):
                layers[k]=v
        return Layers(layers)    
    
    def __init__(self, struct):
        dict.__init__(self, struct)

    def validate(self, errors):
        for k in self:
            if not k.endswith("-layer-arn"):
                errors.append("invalid layer key: %s" % k)

    @property
    def names(self):
        return ["-".join(k.split("-")[:-2])
                for k in self]

class Topics(dict):

    @classmethod
    def initialise(self, parameters):
        topics={}
        for k, v in parameters.items():
            if (isinstance(v, str) and
                v.startswith("arn:aws:sns:")):
                topics[k]=v
        return Topics(topics)    
    
    def __init__(self, struct):
        dict.__init__(self, struct)

    def validate(self, errors):
        for k in self:
            if not k.endswith("-topic-arn"):
                errors.append("invalid topic key: %s" % k)

    @property
    def names(self):
        return ["-".join(k.split("-")[:-2])
                for k in self]
    
class Parameters(dict):

    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def layers(self):
        return Layers.initialise(self)

    def validate_layers(self, errors):
        self.layers.validate(errors)

    @property
    def topics(self):
        return Topics.initialise(self)

    def validate_topics(self, errors):
        self.topics.validate(errors)

            
    def validate(self):
        errors=[]
        for fn in [self.validate_layers,
                   self.validate_topics]:
            fn(errors)
        if errors!=[]:
            raise RuntimeError(", ".join(errors))
        return self
        
    @property
    def parameters(self):
        return {hungarorise(k):v
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

    def validate_action_event_sources(self, errors):
        bucketnames=[bucket["name"] for bucket in self.buckets]        
        tablenames=[table["name"] for table in self.tables]
        for action in self.actions:
            if "events" in action:
                for event in action["events"]:
                    if "source" in event:
                        source=event["source"]
                        if (source["type"]=="bucket" and
                            source["name"] not in bucketnames):
                            errors.append("%s/%s event has bad bucket reference: %s" % (action["name"],
                                                                                        event["name"],
                                                                                        source["name"]))
                        elif (source["type"]=="table" and
                              source["name"] not in tablenames):
                            errors.append("%s/%s event has bad table reference: %s" % (action["name"],
                                                                                       event["name"],
                                                                                       source["name"]))
                            
            
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

    """
    - errors are redefined at each point in the loop as some of these validation functions are conditional
    """
                
    def validate(self):
        for fn in [self.validate_names,
                   self.validate_refs,
                   self.validate_action_event_sources,
                   self.validate_api_endpoints]:
            errors=[]
            fn(errors)
            if errors!=[]:
                raise RuntimeError(", ".join(errors))
        return self

if __name__=="__main__":
    try:
        import json, os, sys
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        from pareto2.dsl import Config
        config=Config.init_file(filename=filename)
        template=config.spawn_template()
        template.init_implied_parameters()
        for validator in [template.parameters.validate,
                          template.validate]:
            try:
                validator()
            except RuntimeError as error:                
                print ("Warning: %s" % str(error))        
        with open("tmp/template.json", 'w') as f:
            f.write(json.dumps(template.render(),
                               indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
