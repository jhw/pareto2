class Component(list):

    def __init__(self, items=[]):
        list.__init__(self, items)

    def render(self):
        resources=dict([resource.render()
                        for resource in self])
        return {"Resources": resources}
