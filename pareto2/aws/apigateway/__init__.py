class Deployment:

    def __init__(self, name):
        self.name = name

    @property
    def resource_name(self):
        return f"{self.name}-deployment"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::Deployment"

    @property
    def aws_properties(self):
        raise NotImplementedError("Subclasses must implement aws_properties")

    @property
    def depends(self):
        raise NotImplementedError("Subclasses must implement depends")

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


class BasePathMapping:

    def __init__(self, name, domain_name="domain-name", stage_name="StageName"):
        self.name = name
        self.domain_name = domain_name
        self.stage_name = stage_name

    @property
    def resource_name(self):
        return f"{self.name}-domain-path-mapping"

    @property
    def aws_resource_type(self):
        return "AWS::ApiGateway::BasePathMapping"

    @property
    def aws_properties(self):
        return {
            "DomainName": {"Ref": self.domain_name},
            "RestApiId": {"Ref": f"{self.name}-rest-api"},
            "Stage": self.stage_name
        }

    @property
    def depends(self):
        return [f"{self.name}-domain"]
