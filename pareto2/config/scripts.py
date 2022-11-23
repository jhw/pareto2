import jsonschema, re, yaml

InfraSchema=yaml.safe_load("""
"$schema": "http://json-schema.org/draft-07/schema#"
type: object
definitions:
  callback:
    type: object
    properties:
      type:
        type: string
        enum:
        - oncreate
      body:
        type: object
    required:
    - type
    - body
    additionalProperties: false
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
    pattern: "^\\\\w+\\\\:\\\\w+$"
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
properties:
  endpoint:
    type: object
    properties: 
      name:
        type: string    
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
    - name
    - api
    - method
    - path
    additionalProperties: false
  callbacks:
    type: array
    items:
      "$ref": "#/definitions/callback"
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
required: []
additionalProperties: false
""")

class Scripts(list):
    
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
                    "userpool": "api",
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
                apiname=endpoint["api"]
                apis[apiname]=init_api(apiname)
        return list(apis.values())
                
    @property
    def buckets(self):
        buckets={}
        for script in self:
            buckets.update({bucket["name"]:bucket
                           for bucket in script.buckets})
        return list(buckets.values())
        
    @property
    def secrets(self):
        secrets={}
        for script in self:
            secrets.update({secret["name"]:secret
                           for secret in script.secrets})
        return list(secrets.values())

    @property
    def tables(self):
        tables={}
        for script in self:
            tables.update({table["name"]:table
                           for table in script.tables})
        return list(tables.values())

    @property
    def topics(self):
        topics={}
        for _script in self:
            topics.update({topic["name"]:topic
                           for topic in script.topics})
        return list(topics.values())

    @property
    def userpools(self):
        for script in self:
            if "endpoint" in script.infra:
                endpoint=script.infra["endpoint"]
                apiname=endpoint["api"]
                if "private" in apiname:
                    return [{"name": "api",
                             "type": "userpool"}]
        return []

    @property
    def callbacks(self):
        callbacks=[]
        for script in self:
            actionname=script.action_name
            if "callbacks" in script.infra:                
                for callback in script.infra["callbacks"]:
                    callback["name"]="%s-cb" % script.action_name
                    callback["action"]=script.action_name
                    callbacks.append(callback)
        return callbacks

def dehungarorise(text):
    return "-".join([tok.lower()
                     for tok in text.split("_")])
    
class Script:

    def __init__(self, filename, body):
        self.filename=filename
        self.body=body
        self.envvars=self.filter_envvars(self.body)
        self.infra=self.filter_infra(self.body)
        self.validate()

    def validate(self):
        self.validate_infra()
        if "endpoint" in self.infra:
            self.validate_endpoint()

    def validate_endpoint(self):
        endpoint=self.infra["endpoint"]
        if (("parameters" in endpoint and
             "schema" in endpoint) or
            (endpoint["method"]=="GET" and
             "parameters" not in endpoint) or
            (endpoint["method"]=="POST" and
             "schema" not in endpoint)):
            raise RuntimeError("%s endpoint is mis- configured" % self.filename)

    def validate_infra(self, schema=InfraSchema):
        try:
            jsonschema.validate(instance=self.infra,
                                schema=schema)
        except jsonschema.exceptions.ValidationError as error:
            raise RuntimeError("error validating infra schema: %s" % str(error))
        
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
                            return struct["infra"]
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
        return "-".join(self.filename.split("/")[1:-1])
    
    @property
    def action_path(self):
        return "-".join(self.filename.split("/")[:-1])

    @property
    def action(self):
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
        if "endpoint" in self.infra:
            action["invocation-type"]="apigw"
        return action

    @property
    def buckets(self):
        return [{"name": dehungarorise(varname),
                 "type": "bucket"}
                for varname in self.envvars
                if varname.endswith("_BUCKET")]

    @property
    def secrets(self):
        return [{"name": secret["name"],
                 "values": [secret["value"]],
                 "type": "secret"}
                for secret in self.infra["secrets"]] if "secrets" in self.infra else []
    
    @property
    def tables(self):
        return [{"name": dehungarorise(varname),
                 "streaming": {},
                 "indexes": [],
                 "type": "table"}
                for varname in self.envvars
                if varname.endswith("_TABLE")]

    @property
    def topics(self):
        return [{"name": dehungarorise(varname),
                 "type": "topic"}
                for varname in self.envvars
                if varname.endswith("_TOPIC")]
    
if __name__=="__main__":
    pass

