from pareto2.recipes import Recipe

import jsonschema, os, yaml

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
    file_contents = Assets(pkg_root)
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
                    file_contents[relative_path] = content
    return file_contents

def filter_infra(filename, text):
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
                    raise RuntimeError(f"{filename} has mis- specified infra block")
            else:
                block=[]                        
        elif inblock:
            block.append(row)
    raise RuntimeError(f"{filename} infra block not found")

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

def handle_lambdas(recipe, assets, endpoints):
    for filename, code in assets.items():
        struct = filter_infra(filename, code)
        type = struct.pop("type") if "type" in struct else "root"
        schema = load_schema(type)
        validate_schema(filename = filename,
                        struct = struct,
                        schema = schema)
    
def handle_root(recipe, filename, code, endpoints):
    struct = filter_infra(filename, code)
    schema = load_schema("root")
    validate_schema(filename = filename,
                    struct = struct,
                    schema = schema)
    for attr in ["api", "bucket"]:        
        if (attr in struct and
            "website" in struct):
            raise RuntimeError(f"app can't have both {attr} and website")
    if "api" in struct:
        pass
    if "bucket" in struct:
        pass
    if "builder" in struct:
        pass
    if "queue" in struct:
        pass
    if "table" in struct:
        pass
    if "website" in struct:
        pass
        
    
def generate(pkg_root):
    assets = file_loader("hello")
    if not assets.has_root:        
        raise RuntimeError("assets have no root content")
    recipe, endpoints = Recipe(), []
    handle_lambdas(recipe, assets.lambda_content, endpoints)
    handle_root(recipe, assets.root_filename, assets.root_content, endpoints)

if __name__ == "__main__":
    try:
        generate("hello")
    except RuntimeError as error:
        print ("Error: %s" % str(error))
