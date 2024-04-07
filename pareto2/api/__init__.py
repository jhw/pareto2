from pareto2.recipes import Recipe

from pareto2.recipes.event_timer import EventTimer
from pareto2.recipes.event_worker import EventWorker
from pareto2.recipes.pip_builder import PipBuilder
from pareto2.recipes.stream_table import StreamTable
from pareto2.recipes.task_queue import TaskQueue
from pareto2.recipes.web_api import WebApi
from pareto2.recipes.website import Website

from pareto2.services import hungarorise as H

from pareto2.services.s3 import StreamBucket

import jsonschema, os, re, yaml

AppNamespace = "app"

class Code:

    def __init__(self, text):
        self.text = text

    @property
    def infra(self):
        block, inblock = [], False
        for row in self.text.split("\n"):
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
                        raise RuntimeError("mis- specified infra block")
                else:
                    block=[]                        
            elif inblock:
                block.append(row)
        raise RuntimeError("infra block not found")

    @property
    def env_variables(self):
        cleantext, refs = re.sub("\\s", "", self.text), set()
        for expr in [r"os\.environ\[(.*?)\]",
                     r"os\.getenv\((.*?)\)"]:
            refs.update(set([tok[1:-1].lower().replace("_", "-")
                             for tok in re.findall(expr, cleantext)
                             if tok.upper()==tok]))
        return refs
    
class Assets(dict):

    def __init__(self, pkg_root, item = {}):
        dict.__init__(self, item)
        self.pkg_root = pkg_root

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
    
def file_loader(pkg_root, root_dir=''):
    assets = Assets(pkg_root)
    pkg_full_path = os.path.join(root_dir, pkg_root)
    for root, dirs, files in os.walk(pkg_full_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            full_path = os.path.join(root, file)
            if (full_path == f"{pkg_root}/__init__.py" or
                full_path.endswith("index.py")):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    relative_path = os.path.relpath(full_path, root_dir)
                    assets[relative_path] = Code(content)
    return assets

def load_schema(type, cache = {}):
    if type in cache:
        return cache[type]    
    filename = "/".join(__file__.split("/")[:-1]+["schemas", f"{type}.yaml"])
    if not os.path.exists(filename):
        raise RuntimeError(f"{filename} does not exist")
    cache[type] = yaml.safe_load(open(filename).read())
    return cache[type]

def validate_schema(filename, struct, schema):
    try:
        jsonschema.validate(instance=struct,
                            schema=schema)
    except jsonschema.exceptions.ValidationError as error:
        raise RuntimeError("%s :: error validating schema: %s" % (filename, str(error)))

def insert_event_source(event, namespace = AppNamespace):
    if event["type"] == "bucket":
        event["pattern"]["detail"].setdefault("bucket", {})
        event["pattern"]["detail"]["bucket"]["name"] = {"Ref": H(f"{namespace}-bucket")}
    elif event["type"] == "builder":
        event["pattern"]["detail"]["project-name"] = {"Ref": H(f"{namespace}-project")}
    elif event["type"] == "queue":
        event["pattern"]["source"] = {"Ref": H(f"{namespace}-queue")}
    elif event["type"] == "table":
        event["pattern"]["source"] = {"Ref": H(f"{namespace}-table")}
    elif event["type"] == "unbound":
        if "detail-type" not in event["pattern"]:
            raise RuntimeError("unbound event must have detail-type")
    
"""
Note that worker and timer create namespaces from python paths, whereas endpoint create namespace from endpoint (http) path
"""
    
def handle_lambdas(recipe, assets, endpoints):
    for filename, code in assets.items():
        struct = code.infra
        type = struct.pop("type") if "type" in struct else "root"
        schema = load_schema(type)
        validate_schema(filename = filename,
                        struct = struct,
                        schema = schema)
        struct["handler"] = filename.replace(".py", ".handler") 
        struct["variables"] = {k: {"Ref": H(k)}
                               for k in code.env_variables}
        if type == "endpoint":
            endpoints.append(struct)
        elif type == "worker":
            namespace = "-".join(filename.split("/")[1:-1])
            insert_event_source(struct["event"])
            recipe += EventWorker(namespace = namespace,
                                  worker = struct)
        elif type == "timer":
            namespace = "-".join(filename.split("/")[1:-1])
            recipe += EventTimer(namespace = namespace,
                                 timer = struct)
        else:
            raise RuntimeError(f"type {type} not recognised")
    
def handle_root(recipe, filename, code, endpoints, namespace = AppNamespace):
    struct = code.infra
    schema = load_schema("root")
    validate_schema(filename = filename,
                    struct = struct,
                    schema = schema)
    if ("api" in struct and
        "bucket" in struct and
        struct["bucket"]["public"]):
        raise RuntimeError(f"app can't have both api and public bucket")
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
            recipe.append(StreamBucket(namespace = namespace))
    if "builder" in struct:
        recipe += PipBuilder(namespace = namespace)
    if "queue" in struct:
        recipe += TaskQueue(namespace = namespace)
    if "table" in struct:
        recipe += StreamTable(namespace = namespace)
            
def build_stack(pkg_root):
    assets = file_loader("hello")
    if not assets.has_root:        
        raise RuntimeError("assets have no root content")
    recipe, endpoints = Recipe(), []
    handle_lambdas(recipe, assets.lambda_content, endpoints)
    handle_root(recipe, assets.root_filename, assets.root_content, endpoints)
    return recipe

if __name__ == "__main__":
    try:
        recipe = build_stack("hello")
        template = recipe.render()
        template.populate_parameters()
        template.dump_file("tmp/template.json")
        print (sorted(list(template["Parameters"].keys())))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
