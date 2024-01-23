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

@resource
def init_domain_record_set(website):
    resourcename=H("%s-website-domain-record-set" % website["name"])
    hzname={"Fn::Sub": ["${name}.", {"name": {"Ref": H("domain-name")}}]} # NB note trailing period
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
