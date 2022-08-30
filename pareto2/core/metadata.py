import os, yaml

class Metadata(dict):

    @classmethod
    def initialise(self, filename="config/metadata.yaml"):
        if not os.path.exists(filename):
            raise RuntimeError("metadata.yaml does not exist")
        return Metadata(yaml.safe_load(open(filename).read()))

    def __init__(self, struct):
        dict.__init__(self, struct)

    def validate(self):
        return self

    def expand(self):
        return self

if __name__=="__main__":
    try:
        md=Metadata.initialise()
        md.validate().expand()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
