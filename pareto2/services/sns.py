from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Topic(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def visible(self):
        return True

class Subscription(Resource):

    def __init__(self, namespace, endpoint_namespace):
        self.namespace = namespace
        self.endpoint_namespace = endpoint_namespace

    @property
    def aws_properties(self):
        return {
            "TopicArn": {"Ref": H(f"{self.namespace}-topic")},
            "Protocol": "lambda",
            "Endpoint": {"Fn::GetAtt": [H(f"{self.endpoint_namespace}-function"), "Arn"]}
        }

