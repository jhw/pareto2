import re

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def dehungarorise(text):
    buf, tok = [], ""
    for c in text:
        if c.upper() == c:
            if tok != "":
                buf.append(tok)
            tok = c.lower()
        else:
            tok += c
    if tok != "":
        buf.append(tok)
    return "-".join(buf)
    
def uppercase(text):
    return "_".join([tok.upper()
                     for tok in text.split("-")])

AWSProxyClassFilterFn = lambda x: len(x) == 4 and x[1] == "services"

class Resource:

    @property
    def class_names(self):
        return [str(cls).split("'")[1] for cls in reversed(self.__class__.__mro__)]

    @property
    def aws_proxy_class(self, filterfn = AWSProxyClassFilterFn):
        classnames = self.class_names
        for classname in classnames:
            tokens = classname.split(".")
            if filterfn(tokens):
                return classname
        raise RuntimeError("AWS proxy class not found for %s" % classnames[-1])

    """
    - occasionally a subclassed resource might override resource_name to point to base_resource_name
    - this is so other resources in the same module can refer to this class using standard #{namespace}-#{resource-name} nomenclature, without having to know the name of the specific subclass
    - most common example is SimpleEmailUserPool
    """
    
    @property
    def base_resource_name(self):    
        tokens = self.class_names[-2].split(".") # base class
        return "%s-%s" % (self.namespace, dehungarorise(tokens[-1]))
    
    @property
    def resource_name(self):    
        tokens = self.class_names[-1].split(".") # latest subclass
        return "%s-%s" % (self.namespace, dehungarorise(tokens[-1]))

    @property
    def aws_resource_type(self, irregulars = {"apigateway": "ApiGateway",
                                              "iam": "IAM"}):
        tokens = self.aws_proxy_class.split(".")
        return "::".join(["AWS",
                          irregulars[tokens[-2]] if tokens[-2] in irregulars else hungarorise(tokens[-2]),
                          tokens[-1]]) # class name already hungarorised

    @property
    def aws_properties(self):
        return {}

    @property
    def visible(self):
        return False
    
    def render(self):
        key = hungarorise(self.resource_name)
        body = {"Type": self.aws_resource_type,
                "Properties": self.aws_properties}
        if hasattr(self, "depends"):
            body["DependsOn"] = self.depends
        return (key, body)
