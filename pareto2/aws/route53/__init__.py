class RecordSet:
    
    def __init__(self, name, resource_suffix, domain_name_ref="domain-name"):
        self.name = name
        self.resource_suffix = resource_suffix
        self.domain_name_ref = domain_name_ref

    @property
    def resource_name(self):
        return f"{self.name}-{self.resource_suffix}-domain-record-set"

    @property
    def aws_resource_type(self):
        return "AWS::Route53::RecordSet"

    @property
    def aws_properties(self):
        hzname = {"Fn::Sub": ["${prefix}.${suffix}.", {
            "prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": self.domain_name_ref}]}]},
            "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": self.domain_name_ref}]}]}
        }]}
        dnsname = {"Fn::GetAtt": [f"{self.name}-{self.resource_suffix}-domain", "DistributionDomainName"]}
        hzid = {"Fn::GetAtt": [f"{self.name}-{self.resource_suffix}-domain", "DistributionHostedZoneId"]}
        aliastarget = {
            "DNSName": dnsname,
            "EvaluateTargetHealth": False,
            "HostedZoneId": hzid
        }
        return {
            "HostedZoneName": hzname,
            "Name": {"Ref": self.domain_name_ref},
            "Type": "A",
            "AliasTarget": aliastarget
        }
