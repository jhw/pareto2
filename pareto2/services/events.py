from pareto2.services import hungarorise as H
from pareto2.services import Resource

import json

"""
Rule namespace is just function namespace; any function should only ever be bound to a single event
"""

class Rule(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def target(self):
        return {
            "Id": {"Fn::Sub": f"{self.namespace}-rule-${{AWS::StackName}}"},
            "Arn": {"Fn::GetAtt": [H(f"{self.namespace}-function"), "Arn"]},
        }
        
    @property    
    def aws_properties(self):
        return {
            "Targets": [self.target]
        }

class PatternRule(Rule):

    def __init__(self, namespace, pattern):
        super().__init__(namespace)
        self.pattern = pattern
    
    @property    
    def aws_properties(self):
        props = super().aws_properties
        props.update({
            "EventPattern": self.pattern,        
            "State": "ENABLED"
        })
        return props

class TimerRule(Rule):

    def __init__(self, namespace, schedule, body = {}):
        super().__init__(namespace)
        self.schedule = schedule
        self.body = body

    @property    
    def target(self):
        target = super().target
        target["Input"] = json.dumps(self.body)
        return target
        
    @property    
    def aws_properties(self):
        props = super().aws_properties
        props["ScheduleExpression"] = self.schedule
        return props

