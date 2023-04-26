import boto3, sys

def list_hosted_zones(route53):
    print ("fetching hosted zones")
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_certificates(acm):
    print ("fetching certificates")
    return {cert["DomainName"]:cert["CertificateArn"]
            for cert in acm.list_certificates()["CertificateSummaryList"]}

def list_record_sets(route53, hostedzoneid):
    print ("fetching record sets for %s" % hostedzoneid)
    return route53.list_resource_record_sets(HostedZoneId=hostedzoneid)["ResourceRecordSets"]

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
        acm=boto3.client("acm", region_name="us-east-1") # NB
        certificates=list_certificates(acm)
        certname="*.%s" % hostname
        if certname not in certificates:
            raise RuntimeError("cert %s does not exists" % certname)
        certarn=certificates[certname]
        print ("deleting certificate %s" % certarn)
        print (acm.delete_certificate(CertificateArn=certarn))
        recordsets=list_record_sets(route53, hostedzoneid)
        recordsettypes=[recordset["Type"] for recordset in recordsets]
        recordsettype="CNAME"
        if recordsettype not in set(recordsettypes):
            raise RuntimeError("%s record set not found in hosted zone %s" % (recordsettype, hostedzonename))
        matchingrecordsets=[recordset for recordset in recordsets
                            if recordset["Type"]==recordsettype]
        if len(matchingrecordsets)!=1:
            raise RuntimeError("multiple %s record sets in hosted zone %s" % (recordsettype, hostedzonename))
        recordset=matchingrecordsets[0]
        changebatch={"Changes": [{'Action': 'DELETE',
                                  'ResourceRecordSet': recordset}]}
        print ("deleting CNAME record for %s" % hostedzoneid)
        print (route53.change_resource_record_sets(HostedZoneId=hostedzoneid,
                                                   ChangeBatch=changebatch))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
