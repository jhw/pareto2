from pareto2.services import hungarorise as H

from pareto2.services.iam import *

import importlib

L = importlib.import_module("pareto2.services.lambda")

import json, os, re
                
"""
- a recipe is just a very thin wrapper around list of resources
- it does not contain its own namespace in state because it may need to operate across a number of namespaces, particularly parent/child (eg api/endpoint)
"""

def function_kwargs(endpoint):
    kwargs = {}
    for attr in ["code",
                 "handler",
                 "memory",
                 "timeout",
                 "runtime",
                 "variables",
                 "layers"]:
        if attr in endpoint:
            kwargs[attr] = endpoint[attr]
    return kwargs
    
def wildcard_override(fn):
    def wrapped(*args, **kwargs):
        permissions=fn(*args, **kwargs)
        wildcards=set([permission.split(":")[0]
                       for permission in permissions
                       if permission.endswith(":*")])
        return [permission for permission in permissions
                if (permission.endswith(":*") or
                    permission.split(":")[0] not in wildcards)]
    return wrapped
    
@wildcard_override
def policy_permissions(worker,
                       defaults = ["logs:CreateLogGroup",
                                   "logs:CreateLogStream",
                                   "logs:PutLogEvents"]):
    permissions = set(defaults)
    if "permissions" in worker:
        permissions.update(set(worker["permissions"]))
    return sorted(list(permissions))

class Recipe(list):

    def __init__(self, singletons = []):
        list.__init__(self)
        self.singletons = singletons

    @property
    def resource_names(self):
        return [resource.resource_name
                for resource in self]


    def is_singleton(self, resource):
        resource_name = resource.resource_name
        for pattern in self.singletons:        
            if re.search(pattern, resource_name):
                return True
        return False
    
    def validate_uniqueness(self):
        counts = {}
        for resource in self:
            if not self.is_singleton(resource):
                counts.setdefault(resource.resource_name, 0)
                counts[resource.resource_name] += 1
        duplicates = [k for k, v in counts.items()
                      if v > 1]
        if duplicates != []:
            raise RuntimeError("duplicate resource names: %s" % ", ".join(duplicates))
    
    def validate(self):
        self.validate_uniqueness()
    
    def render(self):
        return Template(self)

class Template(dict):

    def __init__(self, resources):
        dict.__init__(self, {"Parameters": {},
                             "Resources": dict([resource.render()
                                                for resource in resources]),
                             "Outputs": {H(resource.resource_name): {"Value": {"Ref": H(resource.resource_name)}}
                                         for resource in resources
                                         if resource.visible}})

    def init_parameters(self):
        ids = list(self["Resources"].keys())
        refs = self.refs
        self["Parameters"].update({ref: {"Type": "String"}
                                   for ref in refs
                                   if ref not in ids})

    def set_parameter_value(self, key, value):
        if key not in self["Parameters"]:
            raise RuntimeError(f"parameter {key} not found")
        self["Parameters"][key]["Default"] = value

    def update_parameters(self, parameters):
        for key, value in parameters.items():
            self.set_parameter_value(key, value)

    @property
    def is_complete(self):
        for key in self["Parameters"]:
            if "Default" not in self["Parameters"][key]:
                return False
        return True

    @property
    def unpopulated_parameters(self):
        return [key for key in self["Parameters"]
                if "Default" not in self["Parameters"][key]]

    def validate(self):
        if not self.is_complete:
            raise RuntimeError("template has unpopulated parameters: %s" % ", ".join(self.unpopulated_parameters))
    
    @property
    def node_refs(self):
        def is_ref(key, element):
            return (key == "Ref" and
                    type(element) == str and
                    "::" not in str(element))
        def is_getatt(key, element):
            return (key == "Fn::GetAtt" and
                    type(element) == list and
                    len(element) == 2 and
                    type(element[0]) == str and
                    type(element[1]) == str)
        def is_depends(key, element):
            return (key == "DependsOn" and
                    type(element) == list)
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if is_ref(key, subelement):
                        # print (key, subelement)
                        refs.add(subelement)
                    elif is_getatt(key, subelement):
                        # print (key, subelement[0])
                        refs.add(subelement[0])
                    elif is_depends(key, subelement):
                        # print (key, set(subelement))
                        refs.update(subelement)
                    else:
                        filter_refs(subelement, refs)
        refs = set()
        filter_refs(self["Resources"], refs)
        return refs

    @property
    def inline_refs(self):
        def filter_expressions(text):
            return [tok[2:-1]
                    for tok in re.findall("\\$\\{\\w+\\}", text)
                    if tok != tok.lower()]
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    if isinstance(subelement, str):
                        refs.update(set(filter_expressions(subelement)))
                    else:
                        filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if isinstance(subelement, str):
                        refs.update(set(filter_expressions(subelement)))
                    else:
                        filter_refs(subelement, refs)
        refs = set()
        filter_refs(self, refs)
        return refs

    @property
    def refs(self):
        refs = set()
        refs.update(self.node_refs)
        refs.update(self.inline_refs)
        return refs    

    def dump_file(self, filename):
        path = "/".join(filename.split("/")[:-1])
        if not os.path.exists(path):
            os.makedirs(path)
        with open(filename, 'w') as f:
            f.write(json.dumps(self,
                               sort_keys = True,
                               indent = 2))

    def dump_s3(self, s3, bucket_name, key):
        s3.put_object(Bucket = bucket_name,
                      Key = key,
                      Body = json.dumps(self,
                                        sort_keys = True,
                                        indent = 2),
                      ContentType = "application/json")
