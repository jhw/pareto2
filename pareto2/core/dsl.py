from pareto2.core.template import Template

from pareto2.core.components import hungarorise

from datetime import datetime

import os, re, yaml

EndpointJSONSchema="http://json-schema.org/draft-07/schema#"

"""
- would like to dynamically import this stuff, probably based on file paths
- but not confident you'll be able to do that if package is part of a layer (what's the AWS filepath??)
"""

import pareto2.core.components.action
import pareto2.core.components.api
import pareto2.core.components.bucket
import pareto2.core.components.secret
import pareto2.core.components.table
import pareto2.core.components.timer
import pareto2.core.components.topic
import pareto2.core.components.userpool

ComponentModules={"action": pareto2.core.components.action,
                  "api": pareto2.core.components.api,
                  "bucket": pareto2.core.components.bucket,
                  "secret": pareto2.core.components.secret,                  
                  "table": pareto2.core.components.table,
                  "timer": pareto2.core.components.timer,
                  "topic": pareto2.core.components.topic,
                  "userpool": pareto2.core.components.userpool}

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

    def validate_action_types(self, errors):
        def validate_type(self, attr, type, errors):
            actions={action["name"]:action
                     for action in self.actions}
            for component in getattr(self, attr):
                action=actions[component["action"]]
                if action["type"]!=type:
                    errors.append("%s component %s must be bound to %s action" % (attr,
                                                                                  component["action"],
                                                                                  type))
        for attr, type in [("endpoints", "sync"),
                           ("timers", "sync"),
                           ("topics", "async")]:
            if attr in self:
                validate_type(self, attr, type, errors)


    def validate_action_event_config(self, errors):
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
        self.validate_action_types(errors)
        self.validate_action_event_config(errors)
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

    def expand_endpoint_schema(self):
        for api in self.apis:
            for endpoint in api["endpoints"]:
                if (endpoint["method"]=="POST" and
                    "schema" in endpoint):
                    endpoint["schema"]["$schema"]=EndpointJSONSchema
            
    def expand(self):
        self.expand_action_env_vars()
        self.expand_endpoint_schema()
        return self

    def spawn_template(self,                  
                       name="main",
                       modules=ComponentModules,
                       timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
        template=Template(name=name,
                          timestamp=timestamp)
        for component in self:
            mod=modules[component["type"]]
            resourcefn=getattr(mod, "render_resources")
            template.resources.update(resourcefn(component))
            outputfn=getattr(mod, "render_outputs")
            template.outputs.update(outputfn(component))
        return template
    
if __name__=="__main__":
    try:
        config=Config.initialise()
        config.validate().expand()
        print (config)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
