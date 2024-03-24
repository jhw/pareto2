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
                     for tok in re.split("\\-|\\_", text)])

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

    @property
    def resource_name(self):    
        tokens = self.class_names[2].split(".") # base class
        return "%s-%s" % (self.namespace, dehungarorise(tokens[-1]))

    @property
    def aws_resource_type(self, irregulars = {"apigatewayv2": "ApiGatewayV2",
                                              "dynamodb": "DynamoDB",
                                              "iam": "IAM",
                                              "sns": "SNS",
                                              "sqs": "SQS"}):
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

"""
- AltNamespaceMixin allows subclasses to be referenced via their subclass names rather than their base class names
- it's normally more useful to reference from base class names, but there are a couople of cases where subclass naming is useful
- generally where -
- a) you have more than one subclass of a particular resource
- b) you need instances of more than one subclass in a particular namespace
- examples -
- 1) apigateway 4XX|5XX gateway responses
- 2) website recipe requiring S3 proxy method and also root redirect method
"""

"""
- note that a simple has-many relationship (eg endpoints to apis in webapi receipe) doesn't strictly meet condition b)
"""
    
class AltNamespaceMixin:

    @property
    def resource_name(self):    
        tokens = self.class_names[-1].split(".") # latest subclass
        return "%s-%s" % (self.namespace, dehungarorise(tokens[-1]))
    
