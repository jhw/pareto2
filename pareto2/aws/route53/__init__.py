from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class RecordSet(Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        hzname = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}, # global
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]} # global
        }]}
        dnsnameref = {"Fn::GetAtt": [H(f"{self.component_name}-domain-name"), "DistributionDomainName"]} # APIGW
        hzidref = {"Fn::GetAtt": [H(f"{self.component_name}-domain-name"), "DistributionHostedZoneId"]} # APIGW
        aliastarget = {
            "DNSName": dnsnameref,
            "EvaluateTargetHealth": False,
            "HostedZoneId": hzidref
        }
        return {
            "HostedZoneName": hznameref,
            "Name": {"Ref": H("domain-name")}, # global
            "Type": "A",
            "AliasTarget": aliastarget
        }
