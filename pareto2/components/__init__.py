class Template:

    def __init__(self):
        self.resources=[]

    def add(self, resource):
        self.resources.append(resource)
    
    def render(self):
        resources=dict([resource.render()
                        for resource in self.resources])
        return {"Parameters": {},
                "Resources": resources,
                "Outputs": {}}
