class Components(list):

    def __init__(self, struct=[]):
        list.__init__(self, struct)

    def subset(self, type):
        return [component
                for component in self
                if component["type"]==type]
        
    @property
    def actions(self):
        return self.subset(type="action")
    @property
    def apis(self):
        return self.subset(type="api")
    @property
    def buckets(self):
        return self.subset(type="bucket")
    @property
    def builders(self):
        return self.subset(type="builder")
    @property
    def secrets(self):
        return self.subset(type="secret")
    @property
    def tables(self):
        return self.subset(type="table")
    @property
    def topics(self):
        return self.subset(type="topic")
    @property
    def users(self):
        return self.subset(type="users")
    @property
    def websites(self):
        return self.subset(type="websites")

    @property
    def endpoints(self):
        endpoints=[]
        for api in self.apis:
            if "endpoints" in api:
                endpoints+=api["endpoints"]
        return endpoints

    @property
    def events(self):
        events=[]
        for action in self.actions:
            if "events" in action:
                events+=action["events"]
        return events
    
if __name__=="__main__":
    pass
