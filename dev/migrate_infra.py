import os, re, yaml

Alarm = {
    "period": 60,
    "threshold": 10
}

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

"""
- method: GET
  path: public-get
  auth: public
  parameters:
  - message
  permissions:
  - s3:GetObject
"""

def handle_endpoint(struct, modstruct):
    pass

@insert_alarm
def handle_events(struct, modstruct):
    events = struct["events"]
    if len(events) > 1:
        raise RuntimeError("multiple events detected - %s" % struct)
    event = events.pop()
    modstruct["event"] = {
        "type": event["source"]["type"],
        "pattern": event["pattern"]
    }

"""
event:
  schedule: "rate(1 minute)"
"""
    
def handle_timer(struct, modstruct):
    pass

"""
event:
  pattern:
    source:
    - Ref: HelloQueue
"""

@insert_alarm
def handler_queue(struct, modstruct):
    pass

"""
a topic worker now has no event
"""

@insert_alarm
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
                    handle_infra(struct, modstruct)
                    print (f"--- {relative_path} ---")                    
                    print (yaml.safe_dump(modstruct))

if __name__ == "__main__":
    file_loader("../expander2/expander2")



