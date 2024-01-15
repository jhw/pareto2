from pareto2.dsl.script import Script

class Scripts(list):

    @classmethod
    def initialise(self, assets):
        return Scripts([Script(*asset)
                        for asset in assets])
    
    def __init__(self, items=[]):
        list.__init__(self, items)

    @property
    def apis(self, stagename="prod"):
        def init_public(apiname):
            return {"name": apiname,
                    "type": "api",
                    "endpoints": [],
                    "stage": {"name": stagename},
                    "auth-type": "open"}
        def init_private(apiname):
            return {"name": apiname,
                    "type": "api",
                    "endpoints": [],
                    "stage": {"name": stagename},
                    "user": "api",
                    "auth-type": "cognito"}
        def init_api(apiname):
            for pat, fn in [("public", init_public),
                            ("private", init_private)]:
                if pat in apiname:
                    return fn(apiname)
            raise RuntimeError("no api initialiser for '%s'" % apiname)
        apis={}
        for script in self:
            if "endpoint" in script.infra:
                endpoint=script.infra["endpoint"]
                endpoint["name"]="-".join([tok
                                           for tok in endpoint["path"].split("/")
                                           if tok!=''])
                apiname=endpoint["api"]
                apis[apiname]=init_api(apiname)
        return list(apis.values())

    def aggregate(self, attr):
        items={}
        for script in self:
            items.update({item["name"]:item
                          for item in getattr(script, attr)})
        return (list(items.values()))
        
    @property    
    def buckets(self):
        return self.aggregate("buckets")

    @property
    def queues(self):
        return self.aggregate("queues")
    
    @property
    def tables(self):
        return self.aggregate("tables")

    @property
    def timers(self):
        return self.aggregate("timers")
    
    @property
    def topics(self):
        return self.aggregate("topics")

    @property
    def users(self):
        for script in self:
            if "endpoint" in script.infra:
                endpoint=script.infra["endpoint"]
                apiname=endpoint["api"]
                if "private" in apiname:
                    return [{"name": "api",
                             "type": "user"}]
        return []

    @property
    def websites(self):
        return self.aggregate("websites")
        
if __name__=="__main__":
    pass

