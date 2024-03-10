class Component(list):

    def __init__(self):
        list.__init__(self, [])

    def render(self):
        resources=dict([resource.render()
                        for resource in self])
        return {"Resources": resources}
