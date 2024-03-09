class Component(list):

    def __init__(self, namespace, items=[], **kwargs):
        list.__init__(self, items)
        self.namespace = namespace

    def render(self):
        resources=dict([resource.render()
                        for resource in self])
        return {"Resources": resources}
