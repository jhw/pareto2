import yaml

def hungarorise(text):
    def format_token(text, abbrevs=[]):
        return text.upper() if text in abbrevs else text.capitalize()
    return "".join([format_token(tok)
                    for tok in text.split("-")])

def load_config(filename="config.yaml"):
    return yaml.safe_load(open(filename).read())

if __name__=="__main__":
    pass

