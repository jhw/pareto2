import os, yaml

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

def file_loader(pkg_root, root_dir=''):
    file_contents = []
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
                    file_contents.append((relative_path, content))
    return file_contents

if __name__ == "__main__":
    for filename, code in file_loader("hello"):
        try:
            print ("--- %s ---" % filename)
            print (filter_infra(filename, code))
        except RuntimeError as error:
            print ("Error: %s" % str(error))
