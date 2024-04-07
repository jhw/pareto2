from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Topic(Resource):

    @property
    def visible(self):
        return True
    
class Subscription(Resource):

    @property
    def aws_properties(self):
        return {
            "TopicArn": {"Ref": H(f"{self.namespace}-topic")},
            "Protocol": "lambda",
            "Endpoint": {"Fn::GetAtt": [H(f"{self.namespace}-function"), "Arn"]}
        }

