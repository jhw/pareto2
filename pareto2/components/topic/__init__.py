from pareto2.aws.lambda import Permission as PermissionBase

from pareto2.aws.sns import Topic as TopicBase
from pareto2.aws.sns import TopicPolicy as TopicPolicyBase

class Topic(TopicBase):

    def __init__(self, topic):
        super().__init__(topic["name"])
        self.topic = topic
        self.setup_lambda_subscription()

    def setup_lambda_subscription(self):
        endpoint = {"Fn::GetAtt": [f"{self.topic['action']}-function", "Arn"]}
        subscription = {
            "Protocol": "lambda",
            "Endpoint": endpoint
        }
        self.add_subscription(subscription)

class TopicPolicy(TopicPolicyBase):

    def __init__(self, topic):
        super().__init__(name=topic["name"])
        
class Permission(PermissionBase):
    
    def __init__(self, topic):
        super().__init__(topic["name"],
                         topic["action"],
                         {"Ref": f"{topic['name']}-topic"},
                         "sns.amazonaws.com")
