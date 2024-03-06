from pareto2.aws.apigateway import BasePathMapping
from pareto2.aws.apigateway import DomainName as DomainNameBase
from pareto2.aws.route53 import RecordSet

class DomainName(DomainNameBase):

    def __init__(self, api):
        super().__init__(api["name"])

class DomainBasePathMapping(BasePathMapping):

    def __init__(self, api):
        super().__init__(api["name"], "domain-name", api["stage"]["name"])
        self.api = api

class DomainRecordSet(RecordSet):

    def __init__(self, api):
        super().__init__(api["name"], "api")
