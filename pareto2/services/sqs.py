from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Queue(Resource):

    @property
    def visible(self):
        return True
