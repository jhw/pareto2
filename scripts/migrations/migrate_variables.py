from pareto2.api import file_loader

import os, re, sys

def filter_variables(text):
    cleantext, refs = re.sub("\\s", "", text), set()
    for expr in [r"os\.environ\[(.*?)\]",
                 r"os\.getenv\((.*?)\)",
                 r"self\.env\[(.*?)\]"]:
        refs.update(set([tok[1:-1] for tok in re.findall(expr, cleantext)
                         if tok.upper()==tok]))
    return refs

def migrate_variables(pkg_root):
    for relative_path, text in file_loader(pkg_root):
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



