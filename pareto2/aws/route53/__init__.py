class RecordSet:
    
    def __init__(self, name, resource_suffix, domain_name):
        self.name = name
        self.domain_name = domain_name

    @property
    def resource_name(self):
        return f"{self.name}-record-set"

    @property
    def aws_resource_type(self):
        return "AWS::Route53::RecordSet"

    @property
    def aws_properties(self):
        hzname = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": self.domain_name}]}]},
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": self.domain_name}]}]}
        }]}
        dnsname = {"Fn::GetAtt": [f"{self.name}-record-set", "DistributionDomainName"]}
        hzid = {"Fn::GetAtt": [f"{self.name}-record-set", "DistributionHostedZoneId"]}
        aliastarget = {
            "DNSName": dnsname,
            "EvaluateTargetHealth": False,
            "HostedZoneId": hzid
        }
        return {
            "HostedZoneName": hzname,
            "Name": {"Ref": self.domain_name},
            "Type": "A",
            "AliasTarget": aliastarget
        }
