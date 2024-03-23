from pareto2.services import hungarorise as H

from pareto2.services.iam import *

import importlib

L = importlib.import_module("pareto2.services.lambda")

import re

"""
- LogNamespace is a singleton namespace 
"""

LogNamespace, LogLevels = "logs", ["warning", "error"]

class Template(dict):

    def __init__(self, resources):
        dict.__init__(self, {"Parameters": {},
                             "Resources": dict([resource.render()
                                                for resource in resources]),
                             "Outputs": {H(resource.resource_name): {"Value": {"Ref": H(resource.resource_name)}}
                                         for resource in resources
                                         if resource.visible}})

    def populate_parameters(self):
        ids = list(self["Resources"].keys())
        refs = self.refs
        self["Parameters"].update({ref: {"Type": "String"}
                                   for ref in refs
                                   if ref not in ids})
        
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
    
"""
- a recipe is just a very thin wrapper around list of resources
- it does not contain its own namespace in state because it may need to operate across a number of namespaces, particularly parent/child (eg api/endpoint)
"""

class Recipe(list):

    def __init__(self):
        list.__init__(self)

    def render(self):
        return Template(self)

    def function_kwargs(self, endpoint):
        kwargs = {}
        for attr in ["code",
                     "handler",
                     "memory",
                     "timeout",
                     "runtime",
                     "layers"]:
            if attr in endpoint:
                kwargs[attr] = endpoint[attr]
        return kwargs
    
    def wildcard_override(fn):
        def wrapped(self, *args, **kwargs):
            permissions=fn(self, *args, **kwargs)
            wildcards=set([permission.split(":")[0]
                           for permission in permissions
                           if permission.endswith(":*")])
            return [permission for permission in permissions
                    if (permission.endswith(":*") or
                        permission.split(":")[0] not in wildcards)]
        return wrapped
    
    @wildcard_override
    def policy_permissions(self, worker,
                           defaults = ["logs:CreateLogGroup",
                                       "logs:CreateLogStream",
                                       "logs:PutLogEvents"]):
        permissions = set(defaults)
        if "permissions" in worker:
            permissions.update(set(worker["permissions"]))
        return sorted(list(permissions))

        
