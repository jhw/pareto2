from dev.aws import Resource, hungarorise, dehungarorise

class Whatevs(Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def resource_name(self):    
        tokens=str(self.__class__).split("'")[1].split(".")
        return "%s-%s" % (self.component_name, dehungarorise(tokens[-1]))

    @property
    def aws_resource_type(self):
        tokens=str(self.__class__).split("'")[1].split(".")
        return "::".join([tokens[-3].upper(),
                          hungarorise(tokens[-2]),
                          hungarorise(tokens[-1])])
