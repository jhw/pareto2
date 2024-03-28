from pareto2.services import hungarorise as H
from pareto2.services import Resource

"""
- AWS::ApiGateway::DomainName	DomainName	DistributionDomainName, DistributionHostedZoneId, RegionalDomainName, RegionalHostedZoneId
- AWS::ApiGatewayV2::DomainName	DomainName	RegionalDomainName, RegionalHostedZoneId
"""

"""
^^^ original APIGW supported Distributed (global) domain names; new APIGWV2 does not
Use of Distributed domain names requires certificates in us-east-1; use of Regional domain names does not
Distributed domain names requires the use of Cloudfront; Regional domain names does not
Route53 hopefully much faster now by eschewing use of Distributed domain names (Cloudfront is the slowest service)
"""

class RecordSet(Resource):
    
    def __init__(self, namespace):
        self.namespace = namespace

    @property
    def aws_properties(self):
        hzname = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]},
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}
        }]}
        dnsname = {"Fn::GetAtt": [H(f"{self.namespace}-domain-name"), "RegionalDomainName"]}
        hzidref = {"Fn::GetAtt": [H(f"{self.namespace}-domain-name"), "RegionalHostedZoneId"]}
        aliastarget = {
            "DNSName": dnsname,
            "EvaluateTargetHealth": False,
            "HostedZoneId": hzidref
        }
        return {
            "HostedZoneName": hzname,
            "Name": {"Ref": H("domain-name")}, # global
            "Type": "A",
            "AliasTarget": aliastarget
        }
