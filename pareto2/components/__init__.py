from pareto2.aws import hungarorise as H

class Template(dict):

    def __init__(self, resources):
        dict.__init__(self, {"Parameters": {},
                             "Resources": dict([resource.render()
                                                for resource in resources]),
                             "Outputs": {H(resource.resource_name): {"Value": {"Ref": H(resource.resource_name)}}
                                         for resource in resources
                                         if resource.visible}})

    @property
    def node_references(self):
        def is_ref(key, element):
            return (key=="Ref" and
                    type(element)==str and
                    "::" not in str(element))
        def is_getatt(key, element):
            return (key=="Fn::GetAtt" and
                    type(element)==list and
                    len(element)==2 and
                    type(element[0])==str and
                    type(element[1])==str)
        def is_depends(key, element):
            return (key=="DependsOn" and
                    type(element)==list)
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
        refs=set()
        filter_refs(self["Resources"], refs)
        return refs
        
"""
- a component is just a very thin wrapper around list of resources
- it does not contain its own namespace in state because it may need to operate across a number of namespaces, particularly parent/child (eg api/endpoint)
"""

class Component(list):

    def __init__(self):
        list.__init__(self)

    def render(self):
        return Template(self)
                
