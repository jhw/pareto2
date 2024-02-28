from pareto2.aws.lambda import Permission as PermissionBase

class EventRulePermission(PermissionBase):
    
    def __init__(self, action, event):
        source_arn = {"Fn::GetAtt": [f"{action['name']}-{event['name']}-event-rule", "Arn"]}
        super().__init__(f"{action['name']}-{event['name']}",
                         action["name"],
                         source_arn,
                         "events.amazonaws.com")
