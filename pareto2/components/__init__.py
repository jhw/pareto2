class Component(list):

    def __init__(self, name, items=[], **kwargs):
        list.__init__(self, items)
        self.name = name

    def render(self):
        resources=dict([resource.render()
                        for resource in self])
        return {"Resources": resources}
