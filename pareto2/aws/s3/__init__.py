class Bucket:

    def __init__(self, name, resource_suffix):
        self.name = name
        self.resource_suffix = resource_suffix

    @property
    def resource_name(self):
        return f"{self.name}-{self.resource_suffix}"

    @property
    def aws_resource_type(self):
        return "AWS::S3::Bucket"

    @property
    def aws_properties(self):
        notconf = {"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
        return {"NotificationConfiguration": notconf}
