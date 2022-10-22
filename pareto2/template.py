import re

class Component(dict):

    def __init__(self, item={}):
        dict.__init__(self, item)
        
    """
    - /\\$\\{\\w+\\}/ will exclude double- colon expressions such as `AWS::Region`
    - lowercase check is to remove any local expressions used in Fn::Sub
    """

    @property
    def inline_refs(self):
        def filter_exprs(text):
            return [tok[2:-1]
                    for tok in re.findall("\\$\\{\\w+\\}", text)
                    if tok!=tok.lower()]
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    if isinstance(subelement, str):
                        refs.update(set(filter_exprs(subelement)))
                    else:
                        filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if isinstance(subelement, str):
                        refs.update(set(filter_exprs(subelement)))
                    else:
                        filter_refs(subelement, refs)
        refs=set()
        filter_refs(self, refs)
        return list(refs)

    @property
    def nested_refs(self):
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
                        refs.add(subelement)
                    elif is_getatt(key, subelement):
                        # refs.add("/".join(subelement))
                        refs.add(subelement[0])
                    elif is_depends(key, subelement):
                        refs.update(set(subelement))
                    else:
                        filter_refs(subelement, refs)
        refs=set()
        filter_refs(self, refs)
        return list(refs)

    @property
    def refs(self):
        refs=set()
        for _refs in [self.nested_refs,
                      self.inline_refs]:            
            refs.update(set(_refs))
        return sorted(list(refs))

    @property
    def ids(self):
        return sorted(list(self.keys()))

class Parameter:

    def __init__(self, value=None):
        self.value=value

    @property
    def type(self):
        if (isinstance(self.value, int) or
            re.search("^\\d+$", str(self.value))):
            return "Number"
        else:
            return "String"
        
    def render(self):
        item={"Type": self.type}
        if self.value:
            item["Default"]=self.value
        return item
    
class Parameters(Component):

    def __init__(self, item={}):
        Component.__init__(self, item)

    def update_defaults(self, params):
        for k, v in params.items():
            if k in self:
                self[k]["Default"]=str(v)

    def validate(self, ignore=[]):
        for k, v in self.items():
            if k in ignore:
                pass
            elif "Default" not in v:
                return False
        return True

class Resources(Component):

    def __init__(self, item={}):
        Component.__init__(self, item)

    """
    - resources should only be written to template once
    - possible conflict between names of inline and custom functions, for example
    - hence worth raising an error here
    """
        
    def update(self, item):
        for k in item:
            if k in self:
                raise RuntimeError("duplicate resource key %s" % k)
        Component.update(self, item)
        
class Outputs(Component):

    def __init__(self, item={}):
        Component.__init__(self, item)
    
class Template:

    def __init__(self,
                 version="2010-09-09"):
        self.version=version
        for attr in ["parameters",
                     "resources",
                     "outputs"]:
            klass=eval(attr.capitalize())
            setattr(self, attr, klass())

    """
    - what parameters does a template need, because a resource is referenced within the resources block, but that same resource isn't declared locally; ie needs to be imported ?
    """
                
    def init_implied_parameters(self):
        refs, ids = self.resources.refs, self.resources.ids
        keys=sorted([ref for ref in refs
                     if ref not in ids])
        params={key: Parameter().render()
                for key in keys}
        self.parameters.update(params)

    def render(self):
        return {"AWSTemplateFormatVersion": self.version,
                "Parameters": self.parameters,
                "Resources": self.resources,
                "Outputs": self.outputs}

    def cross_validate_refs(self, errors):
        ids=self.parameters.ids+self.resources.ids
        refs=self.resources.refs+self.outputs.refs
        for ref in refs:
            if ref not in ids:
                errors.append("%s not defined in template" % ref)
                
    def validate_root(self):
        errors=[]
        self.cross_validate_refs(errors)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))

if __name__=="__main__":
    pass
