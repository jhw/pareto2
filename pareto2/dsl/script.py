import jsonschema, re, yaml

InfraSchema=yaml.safe_load(open("/".join(__file__.split("/")[:-1]+["schema.yaml"])))

SQSLookbackPermissions=yaml.safe_load("""
- sqs:DeleteMessage
- sqs:GetQueueAttributes
- sqs:ReceiveMessage
""")
    
class Script:

    def __init__(self, filename, body):
        self.filename=filename
        self.body=body
        self.envvars=self.filter_envvars(self.body)
        self.infra=self.filter_infra(self.body)
        self.validate()

    def validate(self):
        self.validate_infra()
        self.validate_bindings()
        if "endpoint" in self.infra:
            self.validate_endpoint()

    def validate_infra(self, schema=InfraSchema):
        try:
            jsonschema.validate(instance=self.infra,
                                schema=schema)
        except jsonschema.exceptions.ValidationError as error:
            raise RuntimeError("%s error validating infra schema: %s" % (self.filename, str(error)))

    def validate_bindings(self):
        bindings=[]
        for attr in ["endpoint",
                     "events",
                     "queue",
                     "timer",
                     "topic"]:
            if attr in self.infra:
                bindings.append(attr)
        if len(bindings) > 1:
            raise RuntimeError("%s action cannot be bound to %s" % (self.filename, ", ".join(sorted(bindings))))
        
    def validate_endpoint(self):
        endpoint=self.infra["endpoint"]
        if (("parameters" in endpoint and
             "schema" in endpoint) or
            (endpoint["method"]=="GET" and
             "parameters" not in endpoint) or
            (endpoint["method"]=="POST" and
             "schema" not in endpoint)):
            raise RuntimeError("%s endpoint is mis- dslured" % self.filename)

    def filter_infra(self, text):
        block, inblock = [], False
        for row in text.split("\n"):
            if row.startswith('"""'):
                inblock=not inblock
                if not inblock:
                    chunk="\n".join(block)
                    struct=None
                    try:
                        struct=yaml.safe_load(chunk)
                    except:
                        pass
                    if (isinstance(struct, dict) and
                        "infra" in struct):
                        return struct["infra"]
                    elif "infra" in chunk:
                        raise RuntimeError("%s - mis- specified infra block" % self.filename)
                else:
                    block=[]                        
            elif inblock:
                block.append(row)
        raise RuntimeError("%s infra block not found" % self.filename)

    def filter_envvars(self, text):
        return [tok[1:-1]
                for tok in re.findall(r"os\.environ\[(.*?)\]",
                                      re.sub("\\s", "", text))
                if tok.upper()==tok]

    """
    - have experimented with `action-name` being [1:-1] but this tends to obscure topic/queue/timer names [which must be bound to actions]
    """
    
    @property
    def action_name(self):
        # return "-".join(self.filename.split("/")[1:-1])
        return "-".join(self.filename.split("/")[:-1])
    
    @property
    def action_path(self):
        return "-".join(self.filename.split("/")[:-1])

    @property
    def action(self, sqspermissions=SQSLookbackPermissions):
        action={"name": self.action_name,
                "path": self.action_path,            
                "type": "action"}
        for attr in ["layers",
                     "permissions",
                     "events",
                     "size",
                     "timeout"]:
            if attr in self.infra:
                action[attr]=self.infra[attr]
        if "queue" in self.infra:
            action.setdefault("permissions", [])
            action["permissions"]+=sqspermissions
        if ("endpoint" in self.infra or
            "queue" in self.infra):
            action["invocation-type"]="sync"
        return action

    @property
    def bucket_names_env(self):
        return ["-".join([tok.lower()
                          for tok in varname.split("_")[:-1]]) # [NB :-1]
                for varname in self.envvars
                if varname.endswith("_BUCKET")]

    @property
    def bucket_names_event(self):
        names=set()
        if "events" in self.infra:
            for event in self.infra["events"]:
                if ("source" in event and
                    event["source"]["type"] in ["bucket"]):
                    names.add(event["source"]["name"])              
        return names
    
    @property
    def buckets(self):
        bucketnames=set(self.bucket_names_env)
        bucketnames.update(set(self.bucket_names_event))
        return [{"name": bucketname,
                "type": "bucket"}
                for bucketname in list(bucketnames)]

    @property
    def queues(self, batchsize=1):
        return [{"name": self.action_name,
                 "type": "queue",
                 "batch": self.infra["queue"]["batch"] if "batch" in self.infra["queue"] else batchsize,
                 "action": self.action_name}] if "queue" in self.infra else []
    
    @property
    def table_names_env(self):
        return ["-".join([tok.lower()
                          for tok in varname.split("_")[:-1]]) # [NB :-1]
                for varname in self.envvars
                if varname.endswith("_TABLE")]

    @property
    def table_names_event(self):
        names=set()
        if "events" in self.infra:
            for event in self.infra["events"]:
                if ("source" in event and
                    event["source"]["type"]=="table"):
                    names.add(event["source"]["name"])
        return names
    
    @property
    def tables(self):
        tablenames=set(self.table_names_env)
        tablenames.update(set(self.table_names_event))
        return [{"name": tablename,
                 "streaming": {},
                 "indexes": [],
                 "type": "table"}
                for tablename in list(tablenames)]

    @property
    def timers(self):
        return [{"name": self.action_name,
                 "type": "timer",
                 "rate": self.infra["timer"]["rate"],
                 "body": self.infra["timer"]["body"],
                 "action": self.action_name}] if "timer" in self.infra else []
    
    @property
    def topics(self):
        return [{"name": self.action_name,
                 "type": "topic",
                 "action": self.action_name}] if "topic" in self.infra else []

    @property
    def website_names_env(self):
        return ["-".join([tok.lower()
                          for tok in varname.split("_")[:-1]]) # [NB :-1]
                for varname in self.envvars
                if varname.endswith("_WEBSITE")]

    @property
    def website_names_event(self):
        names=set()
        if "events" in self.infra:
            for event in self.infra["events"]:
                if ("source" in event and
                    event["source"]["type"] in ["website"]):
                    names.add(event["source"]["name"])              
        return names
    
    @property
    def websites(self):
        websitenames=set(self.website_names_env)
        websitenames.update(set(self.website_names_event))
        return [{"name": websitename,
                "type": "website"}
                for websitename in list(websitenames)]

    
if __name__=="__main__":
    pass

