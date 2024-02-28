from pareto2.aws.lambda import Permission as PermissionBase

class TopicPermission(PermissionBase):
    
    def __init__(self, topic):
        super().__init__(topic["name"],
                         topic["action"],
                         {"Ref": f"{topic['name']}-topic"},
                         "sns.amazonaws.com")
