from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import Resource

class Queue(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property    
    def aws_properties(self):
        return {}

    @property
    def visible(self):
        return True
