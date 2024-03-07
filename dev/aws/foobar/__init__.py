from dev.aws import Resource, hungarorise, dehungarorise

AWSProxyClassFilterFn=lambda x: len(x)==4 and x[1]=="aws"

class Whatevs(Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def class_names(self):
        return [str(cls).split("'")[1] for cls in self.__class__.__mro__]

    @property
    def aws_proxy_class(self, filterfn=AWSProxyClassFilterFn):
        classnames=self.class_names
        for classname in classnames:
            tokens=classname.split(".")
            if filterfn(tokens):
                return classname
        raise RuntimeError("AWS proxy class not found for %s" % classnames[0])
            
    @property
    def resource_name(self):
        tokens=self.aws_proxy_class.split(".")
        return "%s-%s" % (self.component_name, dehungarorise(tokens[-1]))

    @property
    def aws_resource_type(self):
        tokens=self.aws_proxy_class.split(".")
        return "::".join([tokens[-3].upper(),
                          hungarorise(tokens[-2]),
                          hungarorise(tokens[-1])])
