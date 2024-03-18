from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import Resource

import importlib

lambda_module = importlib.import_module("pareto2.ingredients.lambda")

class Rule(Resource):

    def __init__(self, namespace, function_namespace, pattern):
        self.namespace = namespace
        self.function_namespace = function_namespace
        self.pattern = pattern

    """
    - excluding `-event-rule-` or `-target-id` slugs from target/Id field due to 
    - a) limit of 64 characters for target/Id
    - b) unsure how long ${{AWS::StackName}} might be; but required in case Id is part of global namespace (although probably not)
    - c) no `Fn::Substr|Trim|Truncate` functionality or similar which would allow you to limit string length to 64 characters
    """
        
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

class Permission(lambda_module.Permission):

    def __init__(self, namespace, function_namespace):
        sourcearn={"Fn::GetAtt": [H(f"{self.namespace}-rule"), "Arn"]}
        super().__init__(namespace = function_namespace,    
                         function_namespace = function_namespace,
                         source_arn = source_arn,
                         principal = "events.amazonaws.com")
