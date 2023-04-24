from botocore.exceptions import ClientError

import boto3, sys

def list_hosted_zones(route53):
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_certificates(acm):
    return {cert["DomainName"]:cert["CertificateArn"]
            for cert in acm.list_certificates()["CertificateSummaryList"]}

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
        acm=boto3.client("acm", region_name="us-east-1") # NB
        certificates=list_certificates(acm)
        certname="*.%s" % hostname
        if certname not in certificates:
            raise RuntimeError("cert %s does not exists" % certname)
        certarn=certificates[certname]
        print (acm.delete_certificate(CertificateArn=certificates[certname]))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
