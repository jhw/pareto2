import os, re, yaml

class Asset:

    def __init__(self, filename, text):
        self.filename = filename
        self.infra = self.filter_infra(text)
        self.variables = self.filter_variables(text)

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
                        raise RuntimeError(f"{self.filename} has mis- specified infra block")
                else:
                    block=[]                        
            elif inblock:
                block.append(row)
        raise RuntimeError(f"{self.filename} infra block not found")

    def filter_variables(self, text):
        cleantext, refs = re.sub("\\s", "", text), set()
        for expr in [r"os\.environ\[(.*?)\]",
                     r"os\.getenv\((.*?)\)"]:
            refs.update(set([tok[1:-1].lower().replace("_", "-")
                             for tok in re.findall(expr, cleantext)
                             if tok.upper()==tok]))
        return refs

    def migrate(self):
        if "endpoint" in self.infra:
            self.migrate_endpoint()
        elif "events" in self.infra:
            self.migrate_events()
        elif "timer" in self.infra:
            self.migrate_timer()
        elif "queue" in self.infra:
            self.migrate_queue()
        elif "topic" in self.infra:
            self.migrate_topic()
        else:
            raise RuntimeError("couldn't infer type for {self.filename}")

    def migrate_layers(fn):
        def wrapped(self):
            return fn(self)
        return wrapped

    def migrate_permissions(fn):
        def wrapped(self):
            return fn(self)
        return wrapped

    def migrate_size(fn):
        def wrapped(self):
            return fn(self)
        return wrapped

    def migrate_timeout(fn):
        def wrapped(self):
            return fn(self)
        return wrapped
        
    """
    "endpoint" remains an "endpoint" but format has changed
    """

    @migrate_layers
    @migrate_permissions
    @migrate_size
    @migrate_timeout
    def migrate_endpoint(self):
        print ("endpoint")

    """
    "events" is now a "worker", bound to a single event only
    """

    @migrate_layers
    @migrate_permissions
    @migrate_size
    @migrate_timeout
    def migrate_events(self):
        events = self.infra["events"]
        if len(events) != 1:
            raise RuntimeError(f"{self.filename} has multiple events")
        event = events.pop()
        pattern, source = event["pattern"], event["source"]["type"]
        print (source, pattern)

    """
    "timer" remains a "timer"
    """

    @migrate_layers
    @migrate_permissions
    @migrate_size
    @migrate_timeout
    def migrate_timer(self):
        print ("timer")

    """
    "queue" is now a "worker", with an Eventbridge style message
    """

    @migrate_layers
    @migrate_permissions
    @migrate_size
    @migrate_timeout
    def migrate_queue(self):
        print ("queue")

    """
    "topic" is now a special case of "worker" in which no event is specified
    """

    @migrate_layers
    @migrate_permissions
    @migrate_size
    @migrate_timeout
    def migrate_topic(self):
        print ("topic")
        
class Assets(dict):

    def __init__(self, item = {}):
        dict.__init__(self, item)

def file_loader(pkg_root, root_dir=''):
    assets = Assets()
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
                    assets[relative_path] = Asset(relative_path, content)
    return assets
        
if __name__ == "__main__":
    try:
        assets = file_loader("../expander2/expander2")
        for filename, asset in assets.items():
            print (f"--- {filename} ---")
            # print (asset.infra)
            asset.migrate()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
