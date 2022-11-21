from pareto2.template import Template

from pareto2.components import hungarorise

import json, urllib.request, yaml

import pareto2.components.action
import pareto2.components.api
import pareto2.components.bucket
import pareto2.components.secret
import pareto2.components.table
import pareto2.components.topic
import pareto2.components.userpool

import pareto2.dashboard

ComponentModules={"action": pareto2.components.action,
                  "api": pareto2.components.api,
                  "bucket": pareto2.components.bucket,
                  "secret": pareto2.components.secret,
                  "table": pareto2.components.table,
                  "topic": pareto2.components.topic,
                  "userpool": pareto2.components.userpool}

class Layers(dict):

    @classmethod
    def initialise(self, endpoint):
        url="%s/list-layers" % endpoint
        try:
            layers=json.loads(urllib.request.urlopen(url).read())
        except:
            raise RuntimeError("error reading from %s" % url)
        return Layers({layer["name"]: layer["layer-arn"]
                       for layer in layers})
    
    def __init__(self, item={}):
        dict.__init__(self, item)

    def lookup(self, fragment):
        matches=sorted([key for key in self
                        if key.startswith(fragment)])
        if matches==[]:
            raise RuntimeError("%s not found in layers" % fragment)
        return self[matches.pop()]

class Config(dict):

    @classmethod
    def initialise(self, filename="config.yaml"):
        struct=yaml.safe_load(open(filename).read())
        config=Config({"parameters": Parameters(struct["parameters"]),
                       "components": Components(struct["components"]),
                       "callbacks": Callbacks(struct["callbacks"]),
                       "env": Environment(struct["env"])})
        return config
        
    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        params={}
        for attr in ["parameters"]:
            params.update(self[attr].parameters)
        return params

    def populate_layer_parameters(self, endpoint):
        def filter_layer_refs(actions):
            refs=set()
            for action in actions:
                if "layers" in action:
                    refs.update(set(action["layers"]))
            return list(refs)
        layers=Layers.initialise(endpoint)
        refs=filter_layer_refs(self["components"].actions)
        for ref in refs:
            key="%s-layer-arn" % ref
            layerarn=layers.lookup(ref)
            self["parameters"][key]=layerarn

    def expand(self):
        """
        if "layman-api" in self["env"]:
            self.populate_layer_parameters(self["env"]["layman-api"])
        """
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

class Parameters(dict):

    def __init__(self, struct):
        dict.__init__(self, struct)

    @property
    def layers(self):
        return LayerArns.initialise(self)

    @property
    def topics(self):
        return TopicArns.initialise(self)

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
    def topics(self):
        return [component
                for component in self
                if component["type"]=="topic"]

    @property
    def userpools(self):
        return [component
                for component in self
                if component["type"]=="userpool"]

class Callbacks(list):

    def __init__(self, struct):
        list.__init__(self, struct)

class Environment(dict):

    def __init__(self, struct):
        dict.__init__(self, struct)

if __name__=="__main__":
    try:
        import os, sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter filename")
        filename=sys.argv[1]        
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        config=Config.initialise(filename=filename)
        config.expand()
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
