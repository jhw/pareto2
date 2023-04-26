import boto3, sys, time

def list_hosted_zones(route53):
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_record_sets(route53, hostedzoneid):
    return route53.list_resource_record_sets(HostedZoneId=hostedzoneid)["ResourceRecordSets"]

def list_certificates(acm):
    return {cert["DomainName"]:cert["CertificateArn"]
            for cert in acm.list_certificates()["CertificateSummaryList"]}

"""
- https://github.com/aws/aws-sdk-js/issues/2133
- https://www.2ndwatch.com/blog/use-waiters-boto3-write/
"""

def fetch_resource_record(acm, certarn, maxtries=30, wait=2):
    for i in range(maxtries):
        cert=acm.describe_certificate(CertificateArn=resp["CertificateArn"])["Certificate"]
        if "ResourceRecord" in cert["DomainValidationOptions"][0]:
            return cert["DomainValidationOptions"][0]["ResourceRecord"]
        time.sleep(wait)
    raise RuntimeError("no resource record found for %s" % certarn)
 
if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter hostname")
        hostname=sys.argv[1]
        nperiods=len([c for c in hostname
                      if c=="."])
        if nperiods!=1:            
            raise RuntimeError("hostname can only have a single period")
        if hostname[-1]==".":
            raise RuntimeError("hostname cannot end in period")
        route53=boto3.client("route53")
        hostedzones=list_hosted_zones(route53)
        hostedzonename="%s." % hostname        
        if hostedzonename not in hostedzones:
            raise RuntimeError("hosted zone %s not found" % hostedzonename)
        recordsets=list_record_sets(route53, hostedzones[hostedzonename])
        recordsettypes=set([record["Type"] for record in recordsets])
        if "CNAME" in recordsettypes:
            raise RuntimeError("CNAME already exists in hosted zone %s" % hostedzonename)
        acm=boto3.client("acm", region_name="us-east-1") # NB
        certificates=list_certificates(acm)
        certname="*.%s" % hostname
        if certname in certificates:
            raise RuntimeError("cert %s already exists" % certname)
        resp=acm.request_certificate(DomainName=certname,
                                     ValidationMethod="DNS",
                                     SubjectAlternativeNames=[certname])
        resourcerecord=fetch_resource_record(acm, resp["CertificateArn"])
        print (resourcerecord)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
