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
