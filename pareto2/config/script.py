import re, yaml

class Script:

    def __init__(self, filename):
        self.filename=filename
        self.body=open(filename).read()
        self.infra=self.filter_infra(self.body)
        self.envvars=self.filter_envvars(self.body)

    def filter_infra(self, text):
        def parse_yaml(text):
            return yaml.safe_load(text)
        def is_yaml_dict(text):
            try:
                struct=parse_yaml(text)
                return isinstance(struct, dict)
            except:
                return False
        def is_infra(struct):
            return "infra" in struct
        block, inblock = [], False
        for row in text.split("\n"):
            if row.startswith('"""'):
                inblock=not inblock
                if not inblock:
                    chunk="\n".join(block)
                    if is_yaml_dict(chunk):
                        struct=parse_yaml(chunk)
                        if is_infra(struct):
                            return struct
                else:
                    block=[]                        
            elif inblock:
                block.append(row)
        return None

    def filter_envvars(self, text):
        return [tok[1:-1]
                for tok in re.findall(r"os\.environ\[(.*?)\]",
                                      re.sub("\\s", "", text))
                if tok.upper()==tok]

    @property
    def action_name(self):
        return "-".join(self.filename.split("/")[:-1])

    @property
    def action(self):
        return {"name": self.action_name,
                "type": "action"}

    @property
    def buckets(self):
        return [{"name": "-".join([tok.lower()
                                   for tok in varname.split("_")[:-1]]),
                 "type": "bucket"}
                for varname in self.envvars
                if varname.startswith("BUCKET")]

    @property
    def tables(self):
        return [{"name": "-".join([tok.lower()
                                   for tok in varname.split("_")[:-1]]),
                 "type": "table"}
                for varname in self.envvars
                if varname.startswith("TABLE")]
            
if __name__=="__main__":
    pass

