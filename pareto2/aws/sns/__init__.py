from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Topic(Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

class TopicPolicy(Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        statement = {
            "Effect": "Allow",
            "Principal": {"Service": "sns.amazonaws.com"},
            "Action": ["sns:Publish"],
            "Resource": {"Ref": H(f"{self.component_name}-topic")}
        }
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [statement]
        }
        return {
            "PolicyDocument": policy_doc,
            "Topics": [{"Ref": self._h(f"{self.component_name}-topic")}]
        }

