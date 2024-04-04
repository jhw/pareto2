from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Queue(Resource):

    def __init__(self, namespace):
        super().__init__(namespace)

    @property
    def visible(self):
        return True
