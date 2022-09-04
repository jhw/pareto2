import yaml

if __name__=="__main__":
    config=yaml.safe_load(open("config.yaml").read())
    components=[]
    for action in config["components"]["actions"]:
        action["invocation-type"]=action.pop("type")
    for api in config["components"]["apis"]:
        api["auth-type"]=api.pop("type")
    for groupname in config["components"]:
        for component in config["components"][groupname]:
            component["type"]=groupname[:-1]
            components.append(component)
    config["components"]=sorted(components,
                                key=lambda x: "%s/%s" % (component["type"],
                                                         component["name"]))
    with open("tmp/config.yaml", 'w') as f:
        f.write(yaml.safe_dump(config,
                               default_flow_style=False))
