import json, os, re, yaml

from datetime import datetime

TemplateUrl="https://s3.%s.amazonaws.com/%s/%s-%s.json"

DefaultParameters=yaml.safe_load("""
AppName:
  Type: String
StageName:
  Type: String
""")

class Parameters(dict):

    def __init__(self, items=DefaultParameters):
        dict.__init__(self, items)

class Resources(dict):

    def __init__(self, items={}):
        dict.__init__(self, items)

class Outputs(dict):

    def __init__(self, items={}):
        dict.__init__(self, items)
    
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

    def init_parameters(self, types={}):
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
        return {id: init_param(id, types)
                for id in self.inferred_parameter_ids}

    def autofill_parameters(self,
                            types={}):
        self["Parameters"].update(self.init_parameters(types))
    
    """
    - what parameters does a template need, because a resource is referenced within the resources block, but that same resource isn't declared locally; ie needs to be imported ?
    - note that method doesn't look at existing parameters; is a theoretical ("inferred") construct
    """
    
    @property
    def inferred_parameter_ids(self):
        refs, ids = self.resource_refs, self.resource_ids
        return sorted([ref for ref in refs
                       if ref not in ids])
    
    @property
    def resource_refs(self):
        refs=set()
        refs.update(set(self.nested_refs(["Resources"])))
        refs.update(set(self.inline_refs(["Resources"])))
        return sorted(list(refs))

    @property
    def output_refs(self):
        return self.nested_refs(["Outputs"])

    """
    - /\\$\\{\\w+\\}/ will exclude double- colon expressions such as `AWS::Region`
    - lowercase check is to remove any local expressions used in Fn::Sub
    """
    
    def inline_refs(self, attrs):
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
        for attr in attrs:
            filter_refs(self[attr], refs)
        return list(refs)
    
    def nested_refs(self, attrs):
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
        for attr in attrs:
            filter_refs(self[attr], refs)
        return list(refs)

    @property
    def parameter_ids(self):
        return sorted(self.required_parameter_ids+self.optional_parameter_ids)
    
    @property
    def required_parameter_ids(self):
        return sorted([k for k, v in self["Parameters"].items()
                       if "Default" not in v])

    @property
    def optional_parameter_ids(self):
        return sorted([k for k, v in self["Parameters"].items()
                       if "Default" in v])
    
    @property
    def resource_ids(self):
        return sorted(list(self["Resources"].keys()))

    @property
    def output_ids(self):
        return sorted(list(self["Outputs"].keys()))

    @property
    def metrics(self):
        metrics={k.lower(): len(self[k])
                 for k in ["Parameters",
                           "Resources",
                           "Outputs"]}
        metrics["size"]=len(json.dumps(self))
        return metrics
    
    def validate(self, tempkey, errors):
        ids=self.parameter_ids+self.resource_ids
        refs=self.resource_refs+self.output_refs
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

    """
    - yaml renderers for local dumps
    """

    @property
    def s3_key_yaml(self):
        return "%s-%s.yaml" % (self.name,
                               self.timestamp)

    """
    - json conversion as simple way to clean out classes which pyyaml can't represent
    """
    
    def to_yaml(self):
        return yaml.safe_dump(json.loads(json.dumps(self)),
                              default_flow_style=False)

    @property
    def filename_yaml(self):
        return "tmp/%s-%s.yaml" % (self.name,
                                   self.timestamp)
            
    def dump_yaml(self, filename):
        with open(filename, "w") as f:
            f.write(self.to_yaml())
        
if __name__=="__main__":
    pass
