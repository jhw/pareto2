from pareto2.aws.route53 import RecordSet

class DomainRecordSet(RecordSet):

    def __init__(self, api):
        super().__init__(api["name"], "api")
