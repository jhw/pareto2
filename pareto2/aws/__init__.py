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

"""
def resource(fn):
    def assert_type(type):
        tokens=type.split("::")
        if not ((len(tokens)==3 and
                 tokens[0]=="AWS") or
                (len(tokens)==2 and
                 tokens[0]=="Custom")):
            raise RuntimeError("invalid type %s" % type)
    def assert_props(type, props):
        if not isinstance(props, dict):
            raise RuntimeError("%s props must be a dict" % type)
    def assert_depends(type, depends):
        if not isinstance(depends, list):
            raise RuntimeError("%s depends must be a list" % type)
    def wrapped(*args, **kwargs):
        resp=fn(*args, **kwargs)
        if len(resp)==2:
            resourcename, type = resp
            assert_type(type)
            return (resourcename, {"Type": type,
                                   "Properties": {}})
        elif len(resp)==3:
            resourcename, type, props = resp
            assert_type(type)
            assert_props(type, props)
            return (resourcename, {"Type": type,
                                   "Properties": props})
        elif len(resp)==4:
            resourcename, type, props, depends = resp
            assert_type(type)
            assert_props(type, props)
            assert_depends(type, depends)
            return (resourcename, {"Type": type,
                                   "Properties": props,
                                   "DependsOn": depends})
        else:
            raise RuntimeError("@resource encountered invalid arg profile")
    return wrapped
"""

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
        tokens=self.aws_proxy_class.split(".")
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
        pass
