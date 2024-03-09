from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class RecordSet(Resource):
    
    def __init__(self, name):
        self.name = name

    @property
    def aws_properties(self):
        hzname = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}, # global
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]} # global
        }]}
        dnsname = {"Fn::GetAtt": [H(f"{self.name}-domain-name"), "DistributionDomainName"]} # APIGW
        hzidref = {"Fn::GetAtt": [H(f"{self.name}-domain-name"), "DistributionHostedZoneId"]} # APIGW
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
