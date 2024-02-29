class Method:
    
    def __init__(self, name, aws_resource_type="AWS::ApiGateway::Method", **kwargs):
        self.name = name
        self._aws_resource_type = aws_resource_type
        self.kwargs = kwargs

    @property
    def resource_name(self):
        return f"{self.name}-method"

    @property
    def aws_resource_type(self):
        return self._aws_resource_type

    @property
    def aws_properties(self):
        raise NotImplementedError("Subclasses must implement this property.")

