import os, sys, yaml

if __name__=="__main__":
    try:
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        struct=yaml.safe_load(open(filename).read())
        struct["callbacks"]=[]
        pop_invocation_type(struct)
        with open(filename, 'w') as f:
            f.write(yaml.safe_dump(struct,
                                   default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
