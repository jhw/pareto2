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
    
def uppercase(text):
    return "_".join([tok.upper()
                     for tok in text.split("-")])

class Resource:

    @property
    def class_names(self):
        return [str(cls).split("'")[1] for cls in reversed(self.__class__.__mro__)]

    @property
    def aws_proxy_class(self, filterfn=AWSProxyClassFilterFn):
        classnames=self.class_names
        for classname in classnames:
            tokens=classname.split(".")
            if filterfn(tokens):
                return classname
        raise RuntimeError("AWS proxy class not found for %s" % classnames[-1])
                
    @property
    def resource_name(self):    
        # tokens=self.aws_proxy_class.split(".")
        tokens=str(self.__class__).split(".") # latest subclass
        return "%s-%s" % (self.component_name, dehungarorise(tokens[-1]))

    @property
    def aws_resource_type(self, irregulars={"apigateway": "APIGateway"}):
        tokens=self.aws_proxy_class.split(".")
        return "::".join([tokens[-3].upper(),
                          irregulars[tokens[-2]] if tokens[-2] in irregulars else hungarorise(tokens[-2]),
                          hungarorise(tokens[-1])])

    @property
    def aws_properties(self):
        return {}
    
    def render(self):
        resource={"Type": self.aws_resource_type,
                  "Properties": self.aws_properties}
        if hasattr(self, "depends"):
            resource["DependsOn"]=self.depends
        return (self.resource_name, resource)
