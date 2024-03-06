from pareto2.aws.apigateway import BasePathMapping
from pareto2.aws.apigateway import DomainName as DomainNameBase
from pareto2.aws.route53 import RecordSet

class DomainName(DomainNameBase):

    def __init__(self, website):
        super().__init__(website["name"])

class DomainBasePathMapping(BasePathMapping):

    def __init__(self, website, stagename="StageName"):
        super().__init__(website["name"], "domain-name", stagename)
        self.website = website

class DomainRecordSet(RecordSet):

    def __init__(self, website):
        super().__init__(website["name"], "website")
