from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import Resource

class Rule(Resource):

    def __init__(self, namespace, function_namespace, pattern):
        self.namespace = namespace
        self.function_namespace = function_namespace
        self.pattern = pattern

    @property    
    def aws_properties(self):
        target = {
            "Id": {"Fn::Sub": f"{self.namespace}-${{AWS::StackName}}"},
            "Arn": {"Fn::GetAtt": [H(f"{self.function_namespace}-function"), "Arn"]},
        }
        return {
            "Targets": [target],
            "EventPattern": self.pattern,        
            "State": "ENABLED"
        }
