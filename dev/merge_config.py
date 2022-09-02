import re, yaml
    
if __name__=="__main__":
    with open("tmp/config.yaml", 'w') as f:
        f.write(yaml.safe_dump({"globals": dict([tok.split("=")
                                                 for tok in open("config/app.props").read().split("\n")
                                                 if re.sub("\\s", "", tok)!='']),                
                                "defaults": yaml.safe_load(open("config/defaults.yaml").read()),                
                                "components": yaml.safe_load(open("config/metadata.yaml").read())},
                               default_flow_style=False))
