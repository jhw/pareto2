import json, urllib.request

class Layers(dict):

    @classmethod
    def initialise(self, endpoint):
        url="%s/list-layers" % endpoint
        try:
            layers=json.loads(urllib.request.urlopen(url).read())
        except:
            raise RuntimeError("error reading from %s" % url)
        return Layers({layer["name"]: layer["layer-arn"]
                       for layer in layers})
    
    def __init__(self, item={}):
        dict.__init__(self, item)

    def lookup(self, fragment):
        matches=sorted([key for key in self
                        if key.startswith(fragment)])
        if matches==[]:
            raise RuntimeError("%s not found in layers" % fragment)
        return self[matches.pop()]

if __name__=="__main__":
    pass
    
