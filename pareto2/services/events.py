from pareto2.services import hungarorise as H
from pareto2.services import Resource

"""
Rule namespace is just function namespace; any function should only ever be bound to a single event
"""

class Rule(Resource):

    def __init__(self, namespace, pattern):
        self.namespace = namespace
        self.pattern = pattern
        
    @property    
    def aws_properties(self):
        target = {
            "Id": {"Fn::Sub": f"{self.namespace}-rule-${{AWS::StackName}}"},
            "Arn": {"Fn::GetAtt": [H(f"{self.namespace}-function"), "Arn"]},
        }
        return {
            "Targets": [target],
            "EventPattern": self.pattern,        
            "State": "ENABLED"
        }
