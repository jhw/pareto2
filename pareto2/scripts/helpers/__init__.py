import re

def load_config(filename="config/app.props"):
    return dict([tok.split("=")
                for tok in open(filename).read().split("\n")
                 if re.sub("\\s", "", tok)!=''])

def hungarorise(text):
    def format_token(text, abbrevs="bbc|fd|oc|sb"):
        return text.upper() if text in abbrevs else text.capitalize()
    return "".join([format_token(tok)
                    for tok in text.split("-")])



