import os, re, yaml

def filter_instances(root="pareto2/components"):
    struct={}
    for path, _, filenames in os.walk("pareto2/components"):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            absfilename="%s/%s" % (path, filename)
            for block in  open(absfilename).read().split("\n\n"):
                if block.startswith("@resource"):
                    for match in set(re.findall("\"AWS\\:{2}\\w+\\:{2}\\w+\"", block)):
                        key=match[1:-1].lower().replace("::", "/")
                        struct.setdefault(key, [])
                        struct[key].append((absfilename, block))
    return struct

def format_values(values):
    buf=[]
    for k, v in values:
        buf.append("# %s" % key)
        buf.append(v)
    return "\n\n".join(buf)

if __name__=="__main__":
    struct=filter_instances()
    for key, values in struct.items():
        print (key)
        dirname="tmp/%s" % "/".join(key.split("/")[:-1])
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open("tmp/%s.py" % key, 'w') as f:
            f.write(format_values(values))



            

