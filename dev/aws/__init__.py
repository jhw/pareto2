import re

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def dehungarorise(text):
    buf, tok = [], ""
    for c in text:
        if c.upper()==c:
            if tok!="":
                buf.append(tok)
            tok=c.lower()
        else:
            tok+=c
    if tok!="":
        buf.append(tok)
    return "-".join(buf)

class Resource:

    @property
    def resource_name(self):
        return None

    @property
    def aws_resource_type(self):
        return None
