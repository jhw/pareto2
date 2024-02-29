from pareto2.aws.route53 import RecordSet

class DomainRecordSet(RecordSet):

    def __init__(self, website):
        super().__init__(website["name"], "website")
