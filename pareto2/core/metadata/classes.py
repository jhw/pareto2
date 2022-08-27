from jsonschema import Draft7Validator

import os, re

Draft7Schema="http://json-schema.org/draft-07/schema#"

class ComponentBase(dict):

    def __init__(self, items={}):
        dict.__init__(self, items)

    def validate(self, md, errors):
        pass

    def expand(self, errors):
        pass

class ComponentsBase(list):

    def __init__(self, items=[]):
        list.__init__(self, items)

    @property
    def names(self):
        return [item["name"]
                for item in self]

    def validate_actions(self, md, errors):
        actionnames=md.actions.names
        for component in self:
            if component["action"] not in actionnames:
                errors.append("%s is not a valid action name (component %s)" % (component["action"], component["name"]))

    def validate_buckets(self, md, errors):
        bucketnames=md.buckets.names
        for component in self:
            if component["bucket"] not in bucketnames:
                errors.append("%s is not a valid bucket name (component %s)" % (component["bucket"], component["name"]))
    
    def validate(self, md, errors):
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

    Types=["simple", "cognito"]
    
    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Api(item)
                                       for item in items])

    def validate_types(self, md, errors):
        for api in self:
            if api["type"] not in self.Types:
                errors.append("%s is not a valid api type (api %s)" % (api["type"], api["name"]))
        
    def validate_userpools(self, md, errors):
        userpoolnames=md.userpools.names
        for api in self:
            if (api["type"]=="cognito" and
                api["userpool"] not in userpoolnames):
                errors.append("%s is not a valid userpool name (api %s)" % (api["userpool"], api["name"]))

    def validate_endpoints(self, md, errors):
        allendpointnames=md.endpoints.names
        for api in self:
            for endpointname in api["endpoints"]:
                if endpointname not in allendpointnames:
                    errors.append("%s is not a valid endpoint name (api %s)" % (endpointname, api["name"]))

    def validate(self, md, errors):
        self.validate_types(md, errors)
        self.validate_userpools(md, errors)
        self.validate_endpoints(md, errors)
        
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

class Endpoints(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Endpoint(item)
                                       for item in items])

    def validate(self, md, errors):
        actionnames=md.actions.names
        for endpoint in self:
            if endpoint["action"] not in actionnames:
                errors.append("%s is not a valid action name (endpoint %s)" % (endpoint["action"], endpoint["name"]))
        
    def expand(self, errors):
        for endpoint in self:
            if endpoint["method"]=="POST":
                endpoint.expand_schema(errors)

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
                
class Table(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Tables(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Table(item)
                                       for item in items])

    def validate(self, md, errors):
        actionnames, routernames = md.actions.names, md.routers.names
        for table in self:
            if ("streaming" in table and
                table["streaming"]["router"] not in routernames):
                errors.append("%s is not a valid router name (table %s)" % (table["streaming"]["router"],
                                                                            table["name"]))

class Timer(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Timers(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Timer(item)
                                       for item in items])

    def validate(self, md, errors):
        actionnames=md.actions.names
        for timer in self:
            if timer["action"] not in actionnames:
                errors.append("%s is not a valid action name (timer %s)" % (timer["action"], timer["name"]))

class Topic(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Topics(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Topic(item)
                                       for item in items])

    def validate(self, md, errors):
        actionnames=md.actions.names
        for timer in self:
            if timer["action"] not in actionnames:
                errors.append("%s is not a valid action name (timer %s)" % (timer["action"], timer["name"]))
               
class Userpool(ComponentBase):

    def __init__(self, item={}):
        ComponentBase.__init__(self, item)

class Userpools(ComponentsBase):

    def __init__(self, items=[]):
        ComponentsBase.__init__(self, [Userpool(item)
                                       for item in items])
                
if __name__=="__main__":
    pass
