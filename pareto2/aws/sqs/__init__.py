class Queue:

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def resource_name(self):
        return f"{self.component_name}-queue"

    @property
    def aws_resource_type(self):
        return "AWS::SQS::Queue"

