class Bucket:

    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-bucket"

    @property
    def aws_resource_type(self):
        return "AWS::S3::Bucket"

    @property
    def aws_properties(self):
        notconf = {"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
        return {"NotificationConfiguration": notconf}
