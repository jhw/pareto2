import os, re, yaml

def filter_infra(text):
    blocks = [block for block in text.split('"""')
              if re.sub("\\s", "", block) != ""]
    if blocks == []:
        raise RuntimeError("no infra blocks found")
    try:
        struct = yaml.safe_load(blocks[0])
    except:
        raise RuntimeError("error parsing infra block")
    if "infra" not in struct:
        raise RuntimeError("infra block is mis-specified")
    return struct["infra"]

def handle_layers(fn):
    def wrapped(struct, modstruct):
        modstruct["layers"] = struct["layers"] if "layers" in struct else []
        fn(struct, modstruct)
    return wrapped

def handle_permissions(fn):
    def wrapped(struct, modstruct):
        modstruct["permissions"] = struct["permissions"] if "permissions" in struct else []
        fn(struct, modstruct)
    return wrapped

def handle_size(fn):
    def wrapped(struct, modstruct):
        fn(struct, modstruct)
    return wrapped

def handle_timeout(fn):
    def wrapped(struct, modstruct):
        fn(struct, modstruct)
    return wrapped

def handle_endpoint(struct, modstruct):
    pass

def handle_events(struct, modstruct):
    pass

def handle_timer(struct, modstruct):
    pass
    
def handler_queue(struct, modstruct):
    pass

def handle_topic(struct, modstruct):
    pass

@handle_layers
@handle_permissions
@handle_size
@handle_timeout
def handle_infra(struct, modstruct):
    if "endpoint" in struct:
        handle_endpoint(struct, modstruct)
    elif "events" in struct:
        handle_events(struct, modstruct)
    elif "timer" in struct:
        handle_timer(struct, modstruct)
    elif "queue" in struct:
        handle_queue(struct, modstruct)
    elif "topic" in struct:
        handle_topic(struct, modstruct)
    else:
        raise RuntimeError("no handler found for %s" % struct)
        
    
def file_loader(pkg_root, root_dir=''):
    pkg_full_path = os.path.join(root_dir, pkg_root)
    for root, dirs, files in os.walk(pkg_full_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            full_path = os.path.join(root, file)
            if (full_path == f"{pkg_root}/__init__.py" or
                full_path.endswith("index.py")):
                with open(full_path, 'r', encoding='utf-8') as f:
                    relative_path = os.path.relpath(full_path, root_dir)
                    content = f.read()
                    struct, modstruct = filter_infra(content), {}
                    print (f"--- {relative_path} ---")
                    handle_infra(struct, modstruct)
                    print (modstruct)

if __name__ == "__main__":
    file_loader("../expander2/expander2")



