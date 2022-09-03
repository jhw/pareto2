import json, os, sys, yaml

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter filename")
        filename=sys.argv[1]
        if not filename.endswith(".json"):
            raise RuntimeError("file must be a json file")
        if not os.path.exists(filename):
            raise RuntimeError("file does not exist")
        struct=json.loads(open(filename).read())
        destfilename="tmp/%s" % filename.replace(".json", ".yaml").replace("/", "-")
        with open(destfilename, 'w') as f:
            f.write(yaml.safe_dump(struct,
                                   allow_unicode=True,
                                   default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
                          
