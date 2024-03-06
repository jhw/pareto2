from pareto2.aws.lambda import Permission as PermissionBase

class Permission(PermissionBase):

    def __init__(self, timer):
        super().__init__(timer["name"],
                         timer["action"],
                         {"Fn::GetAtt": [f"{timer['name']}-timer", "Arn"]},
                         "events.amazonaws.com")
