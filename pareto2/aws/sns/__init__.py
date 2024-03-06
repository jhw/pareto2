class Topic:
    
    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-topic"

    @property
    def aws_resource_type(self):
        return "AWS::SNS::Topic"

    @property
    def aws_properties(self):
        return {}

    def add_subscription(self, subscription):
        if "Subscription" not in self.aws_properties:
            self.aws_properties["Subscription"] = []
        self.aws_properties["Subscription"].append(subscription)

class TopicPolicy:

    def __init__(self, name="default"):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-topic-policy"

    @property
    def aws_resource_type(self):
        return "AWS::SNS::TopicPolicy"

    @property
    def aws_properties(self):
        statement = {
            "Effect": "Allow",
            "Principal": {"Service": "sns.amazonaws.com"},
            "Action": ["sns:Publish"],
            "Resource": {"Ref": self._h(f"{self.name}-topic")}
        }
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [statement]
        }
        return {
            "PolicyDocument": policy_doc,
            "Topics": [{"Ref": self._h(f"{self.name}-topic")}]
        }

