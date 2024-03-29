import re

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def uppercase(text):
    return "_".join([tok.upper()
                     for tok in text.split("-")])

"""
- bad stuff happens if you don't have properties
- stuff doesn't get created and then problem is unrectifable even if you add properties later
- it's like the resource is registered somewhere but not created
- see AWS::SQS::Queue
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

if __name__=="__main__":
    pass
