from pareto2.scripts.helpers import hungarorise

class Layers(list):

    @classmethod
    def initialise(self, md):
        return Layers(md.actions.packages)
    
    def __init__(self, items=[]):
        list.__init__(self, items)

    def list_artifacts(self, s3, bucketname,
                       prefix="layer"):
        paginator=s3.get_paginator("list_objects_v2")
        pages=paginator.paginate(Bucket=bucketname,
                                 Prefix=prefix)
        keys=[]
        for struct in pages:
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    keys.append(obj["Key"])
        return keys
        
    def validate(self, s3, config):
        keys=self.list_artifacts(s3, config["ArtifactsBucket"])
        errors=[]
        for pkgname in self:
            key="layer-%s.zip" % pkgname
            if key not in keys:
                errors.append(pkgname)
        if errors!=[]:
            raise RuntimeError("no layer artifacts for %s" % ", ".join(errors))

    @property
    def parameters(self):
        return {hungarorise("layer-key-%s" % pkgname): "layer-%s.zip" % pkgname
                for pkgname in self}

if __name__=="__main__":
    pass
