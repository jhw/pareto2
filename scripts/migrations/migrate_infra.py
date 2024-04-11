
"""
This script migrates pareto 0.6, 0.7 infra snippets to 0.8
"""

import copy, os, re, sys, yaml

Alarm = {
    "period": 60,
    "threshold": 10
}

def file_loader(pkg_root, root_dir='', filter_fn = lambda x: True):
    pkg_full_path = os.path.join(root_dir, pkg_root)
    for root, dirs, files in os.walk(pkg_full_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            full_path = os.path.join(root, file)
            if filter_fn(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    relative_path = os.path.relpath(full_path, root_dir)
                    yield (relative_path, content)

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

def handle_size(fn, sizes = {"default": 512,
                             "large": 2048,
                             "medium": 1024}):
    def wrapped(struct, modstruct):
        key = struct["size"] if "size" in struct else "default"
        modstruct["size"] = sizes[key]
        fn(struct, modstruct)
    return wrapped

def handle_timeout(fn, timeouts = {"default": 5,
                                   "long": 30,
                                   "medium": 15}):        
    def wrapped(struct, modstruct):
        key = struct["timeout"] if "timeout" in struct else "default"
        modstruct["timeout"] = timeouts[key]
        fn(struct, modstruct)
    return wrapped

def insert_alarm(fn, alarm = Alarm):
    def wrapped(struct, modstruct):
        modstruct["alarm"] = alarm
        fn(struct, modstruct)
    return wrapped

def handle_endpoint(struct, modstruct):
    modstruct["type"] = "endpoint"
    endpoint = struct["endpoint"]
    for attr in ["method", "path"]:
        modstruct[attr] = endpoint[attr]
    modstruct["auth"] = endpoint["api"]
    modstruct["parameters"] = endpoint["parameters"] if "parameters" in endpoint else []

@insert_alarm
def handle_events(struct, modstruct):
    modstruct["type"] = "worker"
    events = struct["events"]
    if len(events) > 1:
        raise RuntimeError("multiple events detected - %s" % struct)
    event = events.pop()
    type = event["source"]["type"]
    pattern = copy.deepcopy(event["pattern"])
    for attr in ["diffKeys"]:
        if attr in pattern:
            pattern.pop(attr)
    modstruct["event"] = {
        "type": type,
        "pattern": pattern
    }

def handle_timer(struct, modstruct):
    modstruct["type"] = "timer"
    timer = struct["timer"]
    modstruct["schedule"] = timer["rate"]
    if "body" in struct:
        modstruct["body"] = timer["body"]

"""
A queue worker has an event defined but possibly not a pattern, relying on source binding alone instead
"""
        
@insert_alarm
def handler_queue(struct, modstruct):
    modstruct["type"] = "worker"
    modstruct["event"] = {
        "type": "queue"
    }

"""
A topic worker has no event defined
"""

@insert_alarm
def handle_topic(struct, modstruct):
    modstruct["type"] = "worker"

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

def dump_output(filename, text, struct):
    blocks = [block for block in text.split('"""')
              if re.sub("\\s", "", block) != ""]
    blocks[0] = "\n"+yaml.safe_dump(struct)    
    content = '"""'.join(['']+blocks)
    with open(filename, 'w') as f:
        f.write(content)
    
def migrate_infra(pkg_root):
    for relative_path, content in file_loader(pkg_root,
                                              filter_fn = lambda x: x.endswith("index.py")):
        struct, modstruct = filter_infra(content), {}
        handle_infra(struct, modstruct)
        infra = {"infra": modstruct}
        dump_output(relative_path, content, infra)
                    
if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter path")
        path = sys.argv[1]
        if not os.path.exists(path):
            raise RuntimeError("path does not exist")        
        migrate_infra(path)
    except RuntimeError as error:
        print ("Error: %s" % str(error))



