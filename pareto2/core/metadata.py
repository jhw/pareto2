import os, re, yaml

EndpointJSONSchema="http://json-schema.org/draft-07/schema#"

class Metadata(dict):

    @classmethod
    def initialise(self, filename="config/metadata.yaml"):
        if not os.path.exists(filename):
            raise RuntimeError("metadata.yaml does not exist")
        return Metadata(yaml.safe_load(open(filename).read()))

    def __init__(self, struct):
        dict.__init__(self, struct)

    def validate_refs(self, attr, errors):
        def filter_refs(element, refs, attr):
            if isinstance(element, list):
                for subelement in element:
                    filter_refs(subelement, refs, attr)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if key==attr:
                        refs.add(subelement)
                    else:
                        filter_refs(subelement, refs, attr)
        names=[item["name"]
               for item in self[attr]]
        refs=set()
        filter_refs(self, refs, attr[:-1])
        for ref in refs:
            if ref not in names:
                errors.append("invalid %s reference [%s]" % (attr[:-1], ref))

    def validate_action_type(self, attr, type, errors):
        actions={action["name"]:action
                 for action in self["actions"]}
        if attr in self:
            for component in self[attr]:
                action=actions[component["action"]]
                if action["type"]!=type:
                    errors.append("%s component %s must be bound to %s action" % (attr,
                                                                                  component["action"],
                                                                                  type))
                
    def validate(self):
        errors=[]
        for attr in ["actions",
                     "tables",
                     "buckets"]:
            self.validate_refs(attr, errors)
        for attr, type in [("endpoints", "sync"),
                           ("timers", "sync"),
                           ("topics", "async")]:
            self.validate_action_type(attr, type, errors)
        if errors!=[]:
            raise RuntimeError(", ".join(errors))
        return self

    def expand_action_env_vars(self):
        def expand(action):
            path="%s/index.py" % action["name"].replace("-", "/")
            if not os.path.isfile(path):
                raise RuntimeError("%s handler not found" % action["name"])
            text=open(path).read()
            return [tok[1:-1].lower().replace("_", "-")
                    for tok in re.findall(r"\[(.*?)\]",
                                          re.sub("\\s", "", text))
                    if (tok.upper()==tok and
                        len(tok) > 3)]
        for action in self["actions"]:
            variables=expand(action)
            """
            if variables!=[]:
                print ("%s -> %s" % (action["name"],
                                     ", ".join(variables)))
            """
            action["env"]={"variables": variables}

    def expand_endpoint_schema(self):
        for endpoint in self["endpoints"]:
            if (endpoint["method"]=="POST" and
                "schema" in endpoint):
                endpoint["schema"]["$schema"]=EndpointJSONSchema
            
    def expand(self):
        self.expand_action_env_vars()
        self.expand_endpoint_schema()
        return self

if __name__=="__main__":
    try:
        md=Metadata.initialise()
        md.validate().expand()
    except RuntimeError as error:
        print ("Error: %s" % str(error))