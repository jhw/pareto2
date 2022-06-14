class Parameters(dict):

    @classmethod
    def initialise(self, items):
        params=Parameters()
        for item in items:
            params.update(item)
        return params
    
    def __init__(self, items={}):
        dict.__init__(self, items)

    def validate(self, template):
        errors=[]
        """
        for paramname in self:
            if paramname not in template["Parameters"]:
                errors.append("unknown parameter %s" % paramname)
        """
        for paramname, param in template["Parameters"].items():
            if ("Default" not in param and
                paramname not in self):
                errors.append("missing parameter %s" % paramname)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))
        
    def render(self):
        return [{"ParameterKey": k,
                 "ParameterValue": str(v)} # NB CF requires all values as strings
                for k, v in self.items()]

if __name__=="__main__":
    pass
