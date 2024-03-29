from pareto2.services import hungarorise as H
from pareto2.services import Resource

"""
- AWS::ApiGateway::DomainName	DomainName	DistributionDomainName, DistributionHostedZoneId, RegionalDomainName, RegionalHostedZoneId
- AWS::ApiGatewayV2::DomainName	DomainName	RegionalDomainName, RegionalHostedZoneId
"""

"""
^^^ original APIGW seems to require Distributed (global) domain names; new APIGWV2 only supports Regional ones
"""

class RecordSet(Resource):
    
    def __init__(self, namespace, distribution):
        self.namespace = namespace
        self.distribution = distribution

    @property
    def aws_properties(self):
        hosted_zone_name = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]},
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}
        }]}
        dns_name = {"Fn::GetAtt": [H(f"{self.namespace}-domain-name"), H(f"{self.distribution}-domain-name")]}
        hosted_zone_ref = {"Fn::GetAtt": [H(f"{self.namespace}-domain-name"), H(f"{self.distribution}-hosted-zone-id")]}
        alias_target = {
            "DNSName": dns_name,
            "EvaluateTargetHealth": False,
            "HostedZoneId": hosted_zone_ref
        }
        return {
            "HostedZoneName": hosted_zone_name,
            "Name": {"Ref": H("domain-name")}, # global
            "Type": "A",
            "AliasTarget": alias_target
        }

class DistributedRecordSet(RecordSet):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         distribution = "distributed")

class RegionalRecordSet(RecordSet):

    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         distribution = "regional")

        
