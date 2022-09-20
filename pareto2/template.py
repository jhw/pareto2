import json, os, re

from datetime import datetime

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

    @property
    def mandatory_keys(self):
        return [k for k, v in self.items()
                if "Default" not in v]

    @property
    def optional_keys(self):
        return [k for k, v in self.items()
                if "Default" in v]
        
    def update_defaults(self, params):
        for k, v in params.items():
            if k in self:
                self[k]["Default"]=str(v)

    @property
    def is_complete(self):
        for v in self.values():
            if "Default" not in v:
                return False
        return True

    def validate(self, mandatory=[]):
        params=self.mandatory_keys
        for key in mandatory:
            if key not in params:
                raise RuntimeError("%s not specified as mandatory key" % key)
        if len(params)!=len(mandatory):
            raise RuntimeError("Invalid mandatory parameters - %s" % ", ".join(params))
    
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
                 name="template",
                 version="2010-09-09",
                 timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
        self.name=name
        self.version=version
        self.timestamp=timestamp
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
                errors.append("%s %s not defined" % (self.name, ref))

                
    def validate_root(self):
        errors=[]
        self.cross_validate_refs(errors)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))

    def to_json(self):
        return json.dumps(self.render(),
                          indent=2)

    @property
    def s3_timestamped_key(self):
        return "%s-%s.json" % (self.name,
                               self.timestamp)

    @property
    def s3_latest_key(self):
        return "%s-latest.json" % self.name
    
    def dump_s3(self, s3, bucketname):
        for s3key in [self.s3_timestamped_key,
                      self.s3_latest_key]:
            s3.put_object(Bucket=bucketname,
                          Key=s3key,
                          Body=self.to_json(),
                          ContentType="application/json")

    def dump_local(self):
        with open("tmp/%s" % self.s3_timestamped_key, 'w') as f:
            f.write(self.to_json())
        
if __name__=="__main__":
    pass
