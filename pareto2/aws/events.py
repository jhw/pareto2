from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Rule(Resource):

    def __init__(self, name):
        self.name = name
