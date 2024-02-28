import os, re, yaml

if __name__=="__main__":
    struct={}
    for path, _, filenames in os.walk("pareto2/_components"):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            absfilename="%s/%s" % (path, filename)
            text=open(absfilename).read()
            for match in set(re.findall("\"AWS\\:{2}\\w+\\:{2}\\w+\"", text)):
                key=match[1:-1]
                struct.setdefault(key, [])
                struct[key].append(absfilename)
    print (yaml.safe_dump(struct,
                          default_flow_style=False))

