import os, re, sys

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

def filter_variables(text):
    cleantext, refs = re.sub("\\s", "", text), set()
    for expr in [r"os\.environ\[(.*?)\]",
                 r"os\.getenv\((.*?)\)",
                 r"self\.env\[(.*?)\]"]:
        refs.update(set([tok[1:-1] for tok in re.findall(expr, cleantext)
                         if tok.upper()==tok]))
    return refs

def migrate_variables(pkg_root):
    for relative_path, text in file_loader(pkg_root,
                                           filter_fn = lambda x: x.endswith(".py")):
        variables = filter_variables(text)
        for variable in variables:
            if variable.endswith("_TABLE"):
                text=text.replace(variable, "APP_TABLE")
            elif (variable.endswith("_BUCKET") or
                  variable.endswith("_WEBSITE")):
                text=text.replace(variable, "APP_BUCKET")
            elif (variable.endswith("_BUILDER") or
                  variable.endswith("_PROJECT")):
                text=text.replace(variable, "APP_PROJECT")
            elif variable.endswith("_QUEUE"):
                text=text.replace(variable, "APP_QUEUE")
            elif variable.endswith("_TOPIC"):
                text=text.replace(variable, "_".join(variable.split("_")[1:]))
            else:
                print (f"Warning: unmapped variable {variable}")
        with open(relative_path, 'w') as f:
            f.write(text)

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter path")
        path = sys.argv[1]
        if not os.path.exists(path):
            raise RuntimeError("path does not exist")        
        migrate_variables(path)
    except RuntimeError as error:
        print ("Error: %s" % str(error))



