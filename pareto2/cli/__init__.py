import yaml

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in text.split("-")])

def load_config(filename="config.yaml"):
    return yaml.safe_load(open(filename).read())

if __name__=="__main__":
    pass

