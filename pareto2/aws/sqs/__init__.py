class Queue:

    def __init__(self, queue_name):
        self.queue_name = queue_name

    @property
    def resource_name(self):
        return f"{self.queue_name}-queue"

    @property
    def aws_resource_type(self):
        return "AWS::SQS::Queue"

    @property
    def aws_properties(self):
        """To be overridden by subclasses if additional properties are needed."""
        return {}
