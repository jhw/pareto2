from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_domain(api):
    resourcename=H("%s-api-domain" % api["name"])
    domainname={"Fn::Sub": ["${prefix}.${name}", {"prefix": {"Ref": H("%s-api-domain-prefix" % api["name"])}, "name": {"Ref": H("domain-name")}}]}
    props={"DomainName": domainname,
           "CertificateArn": {"Ref": H("certificate-arn")}}
    return (resourcename,
            "AWS::ApiGateway::DomainName",
            props)

@resource
def init_domain_path_mapping(api):
    resourcename=H("%s-api-domain-path-mapping" % api["name"])
    domainname={"Fn::Sub": ["${prefix}.${name}", {"prefix": {"Ref": H("%s-api-domain-prefix" % api["name"])}, "name": {"Ref": H("domain-name")}}]}
    props={"DomainName": domainname,
           "RestApiId": {"Ref": H("%s-api-rest-api" % api["name"])},
           "Stage": api["stage"]["name"]}
    depends=[H("%s-api-domain" % api["name"])]
    return (resourcename,
            "AWS::ApiGateway::BasePathMapping",
            props,
            depends)

@resource
def init_domain_record_set(api):
    resourcename=H("%s-api-domain-record-set" % api["name"])
    hzname={"Fn::Sub": ["${name}.", {"name": {"Ref": H("domain-name")}}]} # NB note trailing period
    domainname={"Fn::Sub": ["${prefix}.${name}", {"prefix": {"Ref": H("%s-api-domain-prefix" % api["name"])}, "name": {"Ref": H("domain-name")}}]}
    dnsname={"Fn::GetAtt": [H("%s-api-domain" % api["name"]), "DistributionDomainName"]}
    hzid={"Fn::GetAtt": [H("%s-api-domain" % api["name"]), "DistributionHostedZoneId"]}
    aliastarget={"DNSName": dnsname,
                 "EvaluateTargetHealth": False,
                 "HostedZoneId": hzid}
    props={"HostedZoneName": hzname,
           "Name": domainname, # NB `Name` key
           "Type": "A",
           "AliasTarget": aliastarget}
    return (resourcename,
            "AWS::Route53::RecordSet",
            props)

if __name__=="__main__":
    pass
