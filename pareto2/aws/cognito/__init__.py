class UserPool:

    def __init__(self, api):
        self.api = api

    @property
    def resource_name(self):
        return f"{self.api['name']}-api-userpool"

    @property
    def aws_resource_type(self):
        return "AWS::Cognito::UserPool"

    @property
    def aws_properties(self):
        password_policy = {
            "MinimumLength": 8,
            "RequireLowercase": True,
            "RequireNumbers": True,
            "RequireSymbols": True,
            "RequireUppercase": True
        }
        schema = [{
            "AttributeDataType": "String",
            "Mutable": True,
            "Name": "email",
            "Required": True,
            "StringAttributeConstraints": {"MinLength": "1"}
        }]
        return {
            "AutoVerifiedAttributes": ["email"],
            "Policies": {"PasswordPolicy": password_policy},
            "Schema": schema,
            "UsernameAttributes": ["email"]
        }
