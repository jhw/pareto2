class Permission:

    def __init__(self, name, action=None, source_arn=None, principal=None):
        self.name = name
        self.action = action
        self.source_arn = source_arn
        self.principal = principal
    
    @property
    def resource_name(self):
        return f"{self.name}-permission"
    
    @property
    def aws_resource_type(self):
        return "AWS::Lambda::Permission"
    
    @property
    def aws_properties(self):
        props = {
            "Action": "lambda:InvokeFunction",
            "FunctionName": {"Ref": f"{self.action}-function"},
            "Principal": self.principal
        }
        if self.source_arn:
            props["SourceArn"] = self.source_arn
        return props
