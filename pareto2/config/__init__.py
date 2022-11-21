
from pareto2.config.callbacks import Callbacks
from pareto2.config.components import Components
from pareto2.config.environment import Environment
from pareto2.config.layers import Layers
from pareto2.config.parameters import Parameters

from pareto2.template import Template

from pareto2.components import hungarorise

import yaml

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
        print (template.render())
    except RuntimeError as error:
        print ("Error: %s" % str(error))
