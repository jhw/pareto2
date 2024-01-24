from pareto2.components import hungarorise as H
from pareto2.components import resource

StageName="prod"

@resource
def init_domain(website):
    resourcename=H("%s-website-domain" % website["name"])
    props={"DomainName": {"Ref": H("domain-name")},
           "CertificateArn": {"Ref": H("certificate-arn")}}
    return (resourcename,
            "AWS::ApiGateway::DomainName",
            props)

@resource
def init_domain_path_mapping(website, stagename=StageName):
    resourcename=H("%s-website-domain-path-mapping" % website["name"])
    props={"DomainName": {"Ref": H("domain-name")},
           "RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])},
           "Stage": stagename}
    depends=[H("%s-website-domain" % website["name"])]
    return (resourcename,
            "AWS::ApiGateway::BasePathMapping",
            props,
            depends)

"""
- expression for hzname is horrific but is least bad solution given absence of proper string munging facilities in Cloudformation
- alternative would be to have parameters for either DomainPrefix or HostedZone and then use DomainName as a two- token expression, but that just leads to more upstream complexity (as have seen with the earlier use of DomainPrefix)
- not Fn::Select indexes from zero
"""

@resource
def init_domain_record_set(website):
    resourcename=H("%s-website-domain-record-set" % website["name"])
    hzname={"Fn::Sub": ["${prefix}.${suffix}.", {"prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]},
                                                 "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}}]}
    dnsname={"Fn::GetAtt": [H("%s-website-domain" % website["name"]), "DistributionDomainName"]}
    hzid={"Fn::GetAtt": [H("%s-website-domain" % website["name"]), "DistributionHostedZoneId"]}
    aliastarget={"DNSName": dnsname,
                 "EvaluateTargetHealth": False,
                 "HostedZoneId": hzid}
    props={"HostedZoneName": hzname,
           "Name": {"Ref": H("domain-name")}, # NB `Name` key
           "Type": "A",
           "AliasTarget": aliastarget}
    return (resourcename,
            "AWS::Route53::RecordSet",
            props)

if __name__=="__main__":
    pass
