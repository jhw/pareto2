import re, yaml

def dehungarorise(text):
    tokens, tok = [], ""
    for char in text:
        if char.upper()==char:
            if tok!="":
                tokens.append(tok)
            tok=char.lower()
        else:
            tok+=char
    if tok!="":
        tokens.append(tok)
    return "-".join(tokens)

if __name__=="__main__":
    _app=dict([tok.split("=")
              for tok in open("config/app.props").read().split("\n")
              if re.sub("\\s", "", tok)!=''])
    _defaults=yaml.safe_load(open("config/defaults.yaml").read())
    components=yaml.safe_load(open("config/metadata.yaml").read())
    globalz={dehungarorise(k):v
             for k, v in _app.items()
             if "Arn" not in k}
    defaults={dehungarorise(k): v
              for k, v in _defaults.items()}
    layers={dehungarorise(k).split("-")[0]:v
            for k, v in _app.items()
            if "Arn" in k}
    endpoints={endpoint["name"]:endpoint
               for endpoint in components.pop("endpoints")}
    for api in components["apis"]:
        api["endpoints"]=[endpoints[name]
                          for name in api["endpoints"]]
    components.pop("dashboard")
    config={"globals": globalz,
            "defaults": defaults,
            "layers": layers,
            "components": components}
    with open("tmp/config.yaml", 'w') as f:
        f.write(yaml.safe_dump(config, default_flow_style=False))
