from pareto2.cli import hungarorise

class Layers(list):

    @classmethod
    def initialise(self, md):
        return Layers(md.actions.packages)
    
    def __init__(self, items=[]):
        list.__init__(self, items)

    @property
    def parameters(self):
        return {hungarorise("layer-key-%s" % pkgname): "layer-%s.zip" % pkgname
                for pkgname in self}

if __name__=="__main__":
    pass
