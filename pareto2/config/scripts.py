import jsonschema, re, yaml

InfraSchema=yaml.safe_load("""
"$schema": "http://json-schema.org/draft-07/schema#"
type: object
definitions:
  event:
    type: object
    properties: 
      name:
        type: string
      topic:
        type: string
      pattern:
        type: object
      source:
        type: object
        properties:
          name:
            type: string
          type: 
            type: string
            enum:
            - bucket
            - table
        required:
        - name
        - type
        additionalProperties: false
    required:
    - name
    additionalProperties: false
  index:
    type: object
    properties:
      name:
        type: string
      type:
        type: string
        enum:
        - S
      table:
        type: string
    required:
    - name
    - type
    - table
    additionalProperties: false
  layer:
    type: string
  permission:
    type: string
    pattern: "^(\\\\w+\\\\-)*\\\\w+\\\\:(\\\\w+|\\\\*)$"
  queue:
    type: object
    properties:
      batch:
        type: integer
    required:
    - name
    additionalProperties: false
  secret:
    type: object
    properties:
      name:
        type: string
      value:
        type: string
    required:
    - name
    - value
    additionalProperties: false
  timer:
    type: object
    properties:
      rate:
        type: string
      body:
        type: object
    required:
    - rate
    - body
    additionalProperties: false
properties:
  endpoint:
    type: object
    properties: 
      api:
        type: string
      method:
        type: string
        enum:
        - GET
        - POST
      path:
        type: string
      parameters:
        type: array
      schema:
        type: object
    required:
    - api
    - method
    - path
    additionalProperties: false
  events:
    type: array
    items:
      "$ref": "#/definitions/event"
  indexes:
    type: array
    items:
      "$ref": "#/definitions/index"
  layers:
    type: array
    items:
      "$ref": "#/definitions/layer"
  permissions:
    type: array
    items:
      "$ref": "#/definitions/permission"
  queue:
    type: object
    additionProperties: false
  secrets:
    type: array
    items:
      "$ref": "#/definitions/secret"
  size:
    type: string
    enum:
    - default
    - medium
    - large
  timeout:
    type: string
    enum:
    - default
    - medium
    - long
  timer:
    type: object
    additionProperties: false
  topic:
    type: object
    additionProperties: false
required: []
additionalProperties: false
""")

SQSLookbackPermissions=yaml.safe_load("""
- sqs:DeleteMessage
- sqs:GetQueueAttributes
- sqs:ReceiveMessage
""")

class Scripts(list):

    @classmethod
    def initialise(self, assets):
        return Scripts([Script(*asset)
                        for asset in assets])
    
    def __init__(self, items=[]):
        list.__init__(self, items)

    @property
    def apis(self, stagename="1-0-0"):
        def init_public(apiname):
            return {"name": apiname,
                    "type": "api",
                    "endpoints": [],
                    "stage": {"name": stagename},
                    "auth-type": "open"}
        def init_private(apiname):
            return {"name": apiname,
                    "type": "api",
                    "endpoints": [],
                    "stage": {"name": stagename},
                    "user": "api",
                    "auth-type": "cognito"}
        def init_api(apiname):
            for pat, fn in [("public", init_public),
                            ("private", init_private)]:
                if pat in apiname:
                    return fn(apiname)
            raise RuntimeError("no api initialiser for '%s'" % apiname)
        apis={}
        for script in self:
            if "endpoint" in script.infra:
                endpoint=script.infra["endpoint"]
                endpoint["name"]="-".join([tok
                                           for tok in endpoint["path"].split("/")
                                           if tok!=''])
                apiname=endpoint["api"]
                apis[apiname]=init_api(apiname)
        return list(apis.values())

    def aggregate(self, attr):
        items={}
        for script in self:
            items.update({item["name"]:item
                          for item in getattr(script, attr)})
        return (list(items.values()))
        
    @property    
    def buckets(self):
        return self.aggregate("buckets")

    @property
    def queues(self):
        return self.aggregate("queues")
    
    @property
    def secrets(self):
        return self.aggregate("secrets")

    @property
    def tables(self):
        return self.aggregate("tables")

    @property
    def timers(self):
        return self.aggregate("timers")
    
    @property
    def topics(self):
        return self.aggregate("topics")

    @property
    def users(self):
        for script in self:
            if "endpoint" in script.infra:
                endpoint=script.infra["endpoint"]
                apiname=endpoint["api"]
                if "private" in apiname:
                    return [{"name": "api",
                             "type": "user"}]
        return []

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
            raise RuntimeError("%s endpoint is mis- configured" % self.filename)

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
                if event["source"]["type"]=="bucket":
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
    def secrets(self):
        return [{"name": secret["name"],
                 "values": [secret["value"]],
                 "type": "secret"}
                for secret in self.infra["secrets"]] if "secrets" in self.infra else []
    
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
                if event["source"]["type"]=="table":
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
    
if __name__=="__main__":
    pass

