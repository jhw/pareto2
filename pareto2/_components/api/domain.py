from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_domain(api):
    resourcename=H("%s-api-domain" % api["name"])
    props={"DomainName": {"Ref": H("domain-name")},
           "CertificateArn": {"Ref": H("certificate-arn")}}
    return (resourcename,
            "AWS::ApiGateway::DomainName",
            props)

@resource
def init_domain_path_mapping(api):
    resourcename=H("%s-api-domain-path-mapping" % api["name"])
    props={"DomainName": {"Ref": H("domain-name")},
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "Stage": api["stage"]["name"]}
    depends=[H("%s-api-domain" % api["name"])]
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
def init_domain_record_set(api):
    resourcename=H("%s-api-domain-record-set" % api["name"])
    hzname={"Fn::Sub": ["${prefix}.${suffix}.", {"prefix": {"Fn::Select": [1, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]},
                                                 "suffix": {"Fn::Select": [2, {"Fn::Split": [".", {"Ref": H("domain-name")}]}]}}]}
    dnsname={"Fn::GetAtt": [H("%s-api-domain" % api["name"]), "DistributionDomainName"]}
    hzid={"Fn::GetAtt": [H("%s-api-domain" % api["name"]), "DistributionHostedZoneId"]}
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
