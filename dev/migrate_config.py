import os, sys, yaml

def update_event_sources(struct):
    for component in struct["components"]:
        if (component["type"]=="action" and
            "events" in component):
            for event in component["events"]:
                type=event.pop("type")
                if type=="s3":
                    event["source"]={"type": "bucket",
                                     "name": event.pop("bucket")}
                elif type=="dynamodb":
                    event["source"]={"type": "table",
                                     "name": event.pop("table")}
                else:
                    raise RuntimeError("no event source for type %s" % type)

def remove_small_short(struct):
     for component in struct["components"]:         
        if component["type"]=="action":
            for k, v in [("size", "small"),
                         ("timeout", "short")]:
                if component[k]==v:
                    component.pop(k)
                
if __name__=="__main__":
    try:
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        struct=yaml.safe_load(open(filename).read())
        # update_event_sources(struct)
        remove_small_short(struct)
        with open(filename, 'w') as f:
            f.write(yaml.safe_dump(struct,
                                   default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
