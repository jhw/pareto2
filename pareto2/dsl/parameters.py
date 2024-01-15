from pareto2.components import hungarorise

class Parameters(dict):

    def __init__(self, struct={}):
        dict.__init__(self, struct)

    @property
    def parameters(self):
        return {hungarorise(k):v
                for k, v in self.items()}

if __name__=="__main__":
    pass
