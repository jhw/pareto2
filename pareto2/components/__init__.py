class Component(list):

    def __init__(self, items=[]):
        list.__init__(self, items)

    def render(self):
        resources=dict([component.render()
                        for component in self])
        return {"Resources": resources}
