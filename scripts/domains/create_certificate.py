import boto3, sys, time

def list_hosted_zones(route53):
    print ("fetching hosted zones")
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_record_sets(route53, hostedzoneid):
    print ("fetching record sets for %s" % hostedzoneid)
    return route53.list_resource_record_sets(HostedZoneId=hostedzoneid)["ResourceRecordSets"]

def list_certificates(acm):
    print ("fetching certificates")
    return {cert["DomainName"]:cert["CertificateArn"]
            for cert in acm.list_certificates()["CertificateSummaryList"]}

def fetch_resource_record(acm, certarn, maxtries=30, wait=2):
    for i in range(maxtries):
        print ("fetching resource record for %s [%i/%i]" % (certarn,
                                                            i+1,
                                                            maxtries))
        cert=acm.describe_certificate(CertificateArn=resp["CertificateArn"])["Certificate"]
        if ("DomainValidationOptions" in cert and
            cert["DomainValidationOptions"]!=[] and
            "ResourceRecord" in cert["DomainValidationOptions"][0]):
            return cert["DomainValidationOptions"][0]["ResourceRecord"]
        time.sleep(wait)
    raise RuntimeError("no resource record found for %s" % certarn)

def check_certificate_status(acm, certarn, maxtries=40, wait=2, targetstatus="ISSUED"):
    for i in range(maxtries):
        cert=acm.describe_certificate(CertificateArn=certarn)["Certificate"]
        print ("certificate status %s [%i/%i]" % (cert["Status"],
                                                  i+1,
                                                  maxtries))
        if cert["Status"]==targetstatus:
            return
        time.sleep(wait)
    raise RuntimeError("certificate status of %s not realised" % targetstatus)

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
        hostedzoneid=hostedzones[hostedzonename]
        recordsets=list_record_sets(route53, hostedzoneid)
        recordsettypes=set([recordset["Type"] for recordset in recordsets])
        if "CNAME" in recordsettypes:
            raise RuntimeError("CNAME already exists in hosted zone %s" % hostedzonename)
        acm=boto3.client("acm", region_name="us-east-1") # NB
        certificates=list_certificates(acm)
        certdomainname="*.%s" % hostname
        if certdomainname in certificates:
            raise RuntimeError("cert %s already exists" % certdomainname)
        print ("fetching certificate for %s" % certdomainname)
        resp=acm.request_certificate(DomainName=certdomainname,
                                     ValidationMethod="DNS",
                                     SubjectAlternativeNames=[certdomainname])
        certarn=resp["CertificateArn"]
        resourcerecord=fetch_resource_record(acm, certarn)
        resourcerecordset={"Name": resourcerecord["Name"],
                           "Type": "CNAME",
                           "TTL": 300,
                           "ResourceRecords": [{"Value": resourcerecord["Value"]}]}
        changebatch={"Changes": [{'Action': 'CREATE',
                                  'ResourceRecordSet': resourcerecordset}]}
        print ("creating CNAME record for %s" % hostedzoneid)
        print (route53.change_resource_record_sets(HostedZoneId=hostedzoneid,
                                                   ChangeBatch=changebatch))
        print ("checking certificate status")
        check_certificate_status(acm, certarn)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
