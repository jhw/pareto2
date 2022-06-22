from jsonschema import Draft7Validator

from pareto2.cdk.components import uppercase

import os, re, yaml

Draft7Schema="http://json-schema.org/draft-07/schema#"

class ComponentBase(dict):

    def __init__(self, items={}):
        dict.__init__(self, items)

    def validate(self, errors):
        pass

    def expand(self, errors):
        pass

class ComponentsBase(list):

    def __init__(self, items=[]):
        list.__init__(self, items)

    def validate(self, errors):
        pass

    def expand(self, errors):
        pass        
    
class Action(ComponentBase):

    """
    - https://stackoverflow.com/questions/8569201/get-the-string-within-brackets-in-python
    """

    def __init__(self, item={}):    
        ComponentBase.__init__(self, item)
        path="%s/index.py" % item["name"].replace("-", "/")
        if not os.path.isfile(path):
            raise RuntimeError("%s handler not found" % item["name"])
        text=open(path).read()
        variables=[tok[1:-1].lower().replace("_", "-")
                   for tok in re.findall(r"\[(.*?)\]",
                                         re.sub("\\s", "", text))
                   if (tok.upper()==tok and
                       len(tok) > 3)]
        self["env"]={"variables": variables} if variables!=[] else {"variables": []}

class Actions(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Action(item)
                                       for item in items])

    @property
    def names(self):
        return [action["name"]
                for action in self]
            
    @property
    def packages(self):
        packages=set()
        for action in self:
            if "packages" in action:
                packages.update(set(action["packages"]))
        return list(packages)
    
class Api(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Apis(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Api(item)
                                       for item in items])
    
class Bucket(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Buckets(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Bucket(item)
                                       for item in items])
        
class Dashboard(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Endpoint(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

    def validate_schema(fn):
        def wrapped(self, errors):
            fn(self, errors)
            try:
                resp=Draft7Validator.check_schema(self["schema"])
                if resp!=None:
                    raise RuntimeError(resp)
            except Exception as error:
                errors.append("schema validation error: %s" % str(error))
        return wrapped
        
    @validate_schema
    def expand_schema(self, errors):
        from collections import OrderedDict
        schema=OrderedDict()
        schema["$schema"]=Draft7Schema
        schema.update(self["schema"])        
        self["schema"]=schema

    def validate(self, errors):
        if "method" not in self:
            errors.append("%s endpoint has missing method" % self["name"])
        else:
            method=self["method"]
            if method not in ["GET", "POST"]:
                errors.append("%s method is invalid" % self["name"])
            else:
                if method=="GET":
                    if "schema" in self:
                        errors.append("%s GET endpoint can't have schema" % self["name"])                    
                elif method=="POST":
                    if "schema" not in self:
                        errors.append("%s POST endpoint must have schema" % self["name"])
                    if "parameters" in self:
                        errors.append("%s POST endpoint can't have parameters" % self["name"])                    
        
class Endpoints(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Endpoint(item)
                                       for item in items])

    def expand(self, errors):
        for endpoint in self:
            if endpoint["method"]=="POST":
                endpoint.expand_schema(errors)

    def validate(self, errors):
        for endpoint in self:
            endpoint.validate(errors)
                
"""
- NB errors is an instance of action, a specially defined singleton
"""
    
class Errors(Action):

    def __init__(self, item={}):
        Action.__init__(self, item)

    def validate(self, errors):
        pass

    def expand(self, errors):
        pass

class Event(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Events(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Event(item)
                                       for item in items])

class Router(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Routers(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Router(item)
                                       for item in items])

class Secret(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Secrets(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Secret(item)
                                       for item in items])
        
class Userpool(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Userpools(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Userpool(item)
                                       for item in items])
        
class Table(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Tables(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Table(item)
                                       for item in items])

class Timer(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Timers(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Timer(item)
                                       for item in items])

class Metadata:

    SrcPath="config/%s/metadata.yaml"
    
    @classmethod
    def initialise(self, stagename):
        filename=self.SrcPath % stagename
        if not os.path.exists(filename):
            raise RuntimeError("%s metadata does not exist" % stagename)
        return Metadata(stagename, yaml.safe_load(open(filename).read()))

    def __init__(self, stagename, struct):
        self.stagename=stagename
        self.keys=list(struct.keys())
        for k, v in struct.items():
            klass=eval(k.capitalize())
            setattr(self, k, klass(v))

    def validate(self):
        errors=[]
        for k in self.keys:
            getattr(self, k).validate(errors)
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
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        md=Metadata.initialise(stagename)
        md.validate().expand()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
