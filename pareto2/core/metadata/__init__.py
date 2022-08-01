from pareto2.core.components import uppercase

import pareto2.core.metadata.classes

import inspect, os, re, yaml

"""
- if you want to include custom classes in metadata
- add relevant keys to metadata.yaml file
- define custom classes (singular, plural) ahead of md.initialise
"""
                
class Metadata:

    @classmethod
    def initialise(self, extras={}, filename="config/metadata.yaml"):
        if not os.path.exists(filename):
            raise RuntimeError("metadata.yaml does not exist")
        return Metadata(yaml.safe_load(open(filename).read()), extras)

    def __init__(self, struct, extras):
        globalz=dict(inspect.getmembers(pareto2.core.metadata.classes, inspect.isclass))
        globalz.update(extras)
        self.keys=list(struct.keys())
        for k, v in struct.items():
            klass=eval(k.capitalize(), globalz)
            setattr(self, k, klass(v))

    def validate(self):
        errors=[]
        for k in self.keys:
            getattr(self, k).validate(self, errors)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))
        return self

    def expand(self):
        errors=[]
        for k in self.keys:
            getattr(self, k).expand(errors)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))
        return self
        
if __name__=="__main__":
    try:
        md=Metadata.initialise()
        md.validate().expand()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
