import json, os, re, yaml

from datetime import datetime

TemplateUrl="https://s3.%s.amazonaws.com/%s/%s-%s.json"

DefaultParameters=yaml.safe_load("""
AppName:
  Type: String
StageName:
  Type: String
""")

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
    
class Parameters(Component):

    def __init__(self, item=DefaultParameters):
        Component.__init__(self, item)

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
        
class Resources(Component):

    def __init__(self, item={}):
        Component.__init__(self, item)

class Outputs(Component):

    def __init__(self, item={}):
        Component.__init__(self, item)
    
class Template(dict):

    def __init__(self,
                 name="template",
                 timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S"),
                 items={}):
        dict.__init__(self, items)
        self.name=name
        self.timestamp=timestamp
        self["AWSTemplateFormatVersion"]="2010-09-09"        
        for attr in ["Parameters",
                     "Resources",
                     "Outputs"]:
            klass=eval(attr)
            self.setdefault(attr, klass())

    """
    - what parameters does a template need, because a resource is referenced within the resources block, but that same resource isn't declared locally; ie needs to be imported ?
    - note that method doesn't look at existing parameters; is a theoretical ("inferred") construct
    """
    
    @property
    def inferred_parameter_ids(self):
        refs, ids = self["Resources"].refs, self["Resources"].ids
        return sorted([ref for ref in refs
                       if ref not in ids])
            
    def autofill_parameters(self,
                            types={}):
        def param_type(value):
            return "Number" if (isinstance(value, int) or
                                re.search("^\\d+$", str(value))) else "String"
        def render_param(value):
            param={"Type": param_type(value)}
            if value:
                param["Default"]=value
            return param
        def init_param(id, types):
            return render_param(types[id] if id in types else None)
        def init_params(ids, types={}):
            return {id: init_param(id, types)
                    for id in ids}
        ids=self.inferred_parameter_ids
        params=init_params(ids=ids,
                           types=types)
        self["Parameters"].update(params)
            
    @property
    def metrics(self):
        metrics={k.lower(): len(self[k])
                 for k in ["Parameters",
                           "Resources",
                           "Outputs"]}
        metrics["size"]=len(json.dumps(self))
        return metrics
    
    def validate(self, tempkey, errors):
        ids=self["Parameters"].ids+self["Resources"].ids
        refs=self["Resources"].refs+self["Outputs"].refs
        for ref in refs:
            if ref not in ids:
                errors.append("%s %s not defined" % (tempkey, ref))

    def validate_root(self):
        errors=[]
        self.validate(self.name, errors)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))

    def url(self, bucketname):
        if not "AWS_REGION" in os.environ:
            raise RuntimeError("please set AWS_REGION")
        return TemplateUrl % (os.environ["AWS_REGION"],
                              bucketname,
                              self.name,
                              self.timestamp)

    """
    - json renderers for s3
    """

    @property
    def s3_key_json(self):
        return "%s-%s.json" % (self.name,
                               self.timestamp)
    
    def to_json(self):
        return json.dumps(self,
                          indent=2)

    @property
    def filename_json(self):
        return "tmp/%s-%s.json" % (self.name,
                                   self.timestamp)
    
    def dump_json(self, filename):
        with open(filename, "w") as f:
            f.write(self.to_json())

if __name__=="__main__":
    pass
