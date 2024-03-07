from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class RecordSet(Resource):
    
    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def resource_name(self):
        return H(f"{self.component_name}-record-set")

    @property
    def aws_resource_type(self):
        return "AWS::Route53::RecordSet"

    @property
    def aws_properties(self):
        hzname = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]},
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}
        }]}
        dnsnameref = {"Fn::GetAtt": [H(f"{self.component_name}-domain"), "DistributionDomainName"]} # APIGW
        hzidref = {"Fn::GetAtt": [H(f"{self.component_name}-domain"), "DistributionHostedZoneId"]} # APIGW
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
