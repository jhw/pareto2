from pareto2.recipes import Recipe
from pareto2.recipes.event_timer import EventTimer
from pareto2.recipes.event_worker import EventWorker
from pareto2.recipes.pip_builder import PipBuilder
from pareto2.recipes.stream_table import StreamTable
from pareto2.recipes.task_queue import TaskQueue
from pareto2.recipes.web_api import WebApi
from pareto2.recipes.website import Website

from pareto2.services import hungarorise as H
from pareto2.services.s3 import StreamingBucket

import jsonschema, os, re, yaml

"""
Pros and cons to having a single top- level namespace

Pros -> easy for lambda scripts to reference underlying Cloudformation resources

Cons -> recipes which have a lot of resources can pollute one another (eg website and builder both have Role and Policy)

### Solutions

a) ban cross- polluting combinations
b) have more than one top- level namespace
c) each recipe to only have a single component in root namespace

---

b) is superficially appealing but make insertion of event sources into events more complex (because you have to maintain a range of namespaces)

c) is also appealing (esp as streaming-table and task-queue effectively do this already) but means more child namespace complexity at services level

In the end a) may be the least bad solution, esp as the key culprits (website and builder) are what you might call "marginal" components
"""

AppNamespace = "app"

class Project(dict):

    """
    Note filtering; Project may be passed full set of assets but not need everything
    """
    
    def __init__(self, pkg_root, assets):
        dict.__init__(self, {
            path: {
                "infra": self.filter_infra(path, content),
                "variables": self.filter_variables(path, content)
            }
            for path, content in assets.items()
            if (path  == f"{pkg_root}/__init__.py" or
                path.endswith("index.py"))
        })
        self.pkg_root = pkg_root
        
    def filter_infra(self, path, text):
        blocks = [block for block in text.split('"""')
                  if re.sub("\\s", "", block) != ""]
        if blocks == []:
            raise RuntimeError(f"no infra blocks found in {path}")
        try:
            struct = yaml.safe_load(blocks[0])
        except:
            raise RuntimeError(f"error parsing {path} infra block")
        if "infra" not in struct:
            raise RuntimeError(f"{path} infra block is mis-specified")
        return struct["infra"]

    def filter_variables(self, path, text):
        cleantext, refs = re.sub("\\s", "", text), set()
        for expr in [r"os\.environ\[(.*?)\]",
                     r"os\.getenv\((.*?)\)"]:
            refs.update(set([tok[1:-1].lower().replace("_", "-")
                             for tok in re.findall(expr, cleantext)
                             if tok.upper()==tok]))
        return refs
        
    @property
    def root_filename(self):
        return f"{self.pkg_root}/__init__.py"

    @property
    def has_root(self):
        return self.root_filename in self

    @property
    def root_content(self):
        return self[self.root_filename]

    @property
    def lambda_content(self):
        return {k:v for k, v in self.items()
                if k != self.root_filename}

    def load_schema(self, type, cache = {}):
        if type in cache:
            return cache[type]    
        filename = "/".join(__file__.split("/")[:-1]+["schemas", f"{type}.yaml"])
        if not os.path.exists(filename):
            raise RuntimeError(f"{filename} does not exist")
        with open(filename, 'r', encoding='utf-8') as f:
            cache[type] = yaml.safe_load(f.read())
        return cache[type]

    def validate_schema(self, filename, struct, schema):
        try:
            jsonschema.validate(instance=struct,
                                schema=schema)
        except jsonschema.exceptions.ValidationError as error:
            raise RuntimeError("%s :: error validating schema: %s" % (filename, str(error)))
    
    """
    api (obviously) conflicts with public bucket over use of domain name
    builder conflicts with public bucket because both have role, policy in app namespace; no good reason for both to exist the same time
    """
        
    def handle_root(self, recipe, endpoints, namespace = AppNamespace):
        struct = self.root_content["infra"]
        schema = self.load_schema("root")
        self.validate_schema(filename = self.root_filename,
                             struct = struct,
                             schema = schema)
        for attr in ["api", "builder"]:
            if (attr in struct and
                "bucket" in struct and
                struct["bucket"]["public"]):
                raise RuntimeError(f"app can't have both {attr} and public bucket")
        if "api" in struct:
            if endpoints != []:
                recipe += WebApi(namespace = namespace,
                                 endpoints = endpoints)
        if "bucket" in struct:
            if struct["bucket"]["public"]:
                binary_media = struct["bucket"]["binary-media"] if "binary-media" in struct["bucket"] else False
                recipe += Website(namespace = namespace,
                                  binary_media = binary_media)
            else:
                recipe.append(StreamingBucket(namespace = namespace))
        if "builder" in struct:
            recipe += PipBuilder(namespace = namespace)
        if "queue" in struct:
            batch_size = struct["queue"]["batch-size"] if "batch-size" in struct["queue"] else 10
            recipe += TaskQueue(namespace = namespace,
                                batch_size = batch_size)
        if "table" in struct:
            indexes = struct["table"]["indexes"] if "indexes" in struct["table"] else []
            batch_window = struct["table"]["batch-window"] if "batch-table" in struct["table"] else 1
            recipe += StreamTable(namespace = namespace,
                                  indexes = indexes,
                                  batch_window = batch_window)

    def validate_event_attributes(self, event):
        if event["type"] == "unbound":
            if "detail-type" not in event["pattern"]:
                raise RuntimeError("unbound event must have detail-type")
        else:
            if "detail" not in event["pattern"]:
                raise RuntimeError("bound event must have detail")
            
    def insert_event_source(self, event, namespace = AppNamespace):
        if event["type"] == "bucket":
            event["pattern"]["detail"].setdefault("bucket", {})
            event["pattern"]["detail"]["bucket"]["name"] = [{"Ref": H(f"{namespace}-bucket")}]
        elif event["type"] == "builder":
            event["pattern"]["detail"]["project-name"] = [{"Ref": H(f"{namespace}-project")}]
        elif event["type"] == "queue":
            event["pattern"]["source"] = [{"Ref": H(f"{namespace}-queue")}]
        elif event["type"] == "table":
            event["pattern"]["source"] = [{"Ref": H(f"{namespace}-table")}]
            
    """
    Note that worker and timer create namespaces from python paths, whereas endpoint create namespace from endpoint (http) path
    """
    
    def handle_lambdas(self, recipe, endpoints, variables):
        for filename, asset in self.lambda_content.items():
            struct = asset["infra"]
            type = struct.pop("type") if "type" in struct else "root"
            schema = self.load_schema(type)
            self.validate_schema(filename = filename,
                                 struct = struct,
                                 schema = schema)
            struct["handler"] = filename.replace(".py", ".handler") 
            struct["variables"] = {k: {"Ref": H(k)}
                                   for k in asset["variables"]}
            variables.update(struct["variables"])
            if type == "endpoint":
                endpoints.append(struct)
            elif type == "worker":
                namespace = "-".join(filename.split("/")[1:-1])
                if "event" in struct:
                    self.validate_event_attributes(struct["event"])
                    self.insert_event_source(struct["event"])
                recipe += EventWorker(namespace = namespace,
                                      worker = struct)
            elif type == "timer":
                namespace = "-".join(filename.split("/")[1:-1])
                recipe += EventTimer(namespace = namespace,
                                     timer = struct)
            else:
                raise RuntimeError(f"type {type} not recognised")
    
    def post_validate_env_variables(self, recipe, variables):
        resource_names = recipe.resource_names
        missing = [variable for variable in variables
                   if variable not in resource_names]
        if missing != []:
            raise RuntimeError("references to unknown resources: %s" % ", ".join(missing))
    
    def spawn_recipe(self, singletons = ["^alert",
                                         "^alarm",
                                         "^app\\-bucket$"]):    
        recipe, endpoints, variables = Recipe(singletons = singletons), [], set()
        self.handle_lambdas(recipe, endpoints, variables)
        self.handle_root(recipe, endpoints)
        self.post_validate_env_variables(recipe, variables)
        recipe.validate()
        return recipe

    def spawn_template(self, env):
        recipe = self.spawn_recipe()
        template = recipe.render()
        template.init_parameters()
        template.update_parameters(env)
        template.validate()
        return template
    
if __name__ == "__main__":
    pass
        
