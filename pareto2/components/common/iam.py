def policy_document(permissions, resource="*"):
    class Group(list):
        def __init__(self, key, item=[]):
            list.__init__(item)
            self.key=key
        def render(self):
            return ["%s:*" % self.key] if "*" in self else ["%s:%s" % (self.key, value) for value in self]
    def group_permissions(permissions):
        groups={}
        for permission in permissions:
            prefix, suffix = permission.split(":")
            groups.setdefault(prefix, Group(prefix))
            groups[prefix].append(suffix)
        return [group.render()
                for group in list(groups.values())]
    return {"Version": "2012-10-17",
            "Statement": [{"Action" : group,
                           "Effect": "Allow",
                           "Resource": resource}
                          for group in group_permissions(permissions)]}

def assume_role_policy_document(service="lambda.amazonaws.com"):
    return {"Version": "2012-10-17",
            "Statement": [{"Action": "sts:AssumeRole",
                           "Effect": "Allow",
                           "Principal": {"Service": service}}]}

if __name__=="__main__":
    pass
