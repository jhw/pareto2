from pareto2.services import hungarorise as H
from pareto2.services import Resource

import json

"""
Rule namespace is just function namespace; any function should only ever be bound to a single event
"""

"""
ID: The ID of the target within the specified rule (ie local)
"""

class Rule(Resource):

    @property
    def target(self):
        return {
            "Id": {"Fn::Sub": f"{self.namespace}-rule"},
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

    def __init__(self, namespace, rate, body = {}):
        super().__init__(namespace)
        self.rate = rate
        self.body = body

    @property    
    def target(self):
        target = super().target
        target["Input"] = json.dumps(self.body)
        return target

    def format_rate(self, rate):
        number, amount = rate.split(" ")
        if (number == "1" and
            amount.endswith("s")):
            amount = amount[:-1]
        return f"{number} {amount}"
    
    def format_schedule(self, rate):
        formatted_rate = self.format_rate(rate)
        return f"rate({formatted_rate})"
    
    @property    
    def aws_properties(self):
        props = super().aws_properties
        props["ScheduleExpression"] = self.format_schedule(self.rate)
        return props

