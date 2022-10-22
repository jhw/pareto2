import yaml

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

if __name__=="__main__":
    struct=yaml.safe_load(open("config.yaml").read())
    update_event_sources(struct)
    with open("tmp/config.yaml", 'w') as f:
        f.write(yaml.safe_dump(struct,
                               default_flow_style=False))
