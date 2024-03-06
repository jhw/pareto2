class Queue:

    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-queue"

    @property
    def aws_resource_type(self):
        return "AWS::SQS::Queue"

