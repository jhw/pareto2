import boto3

if __name__=="__main__":
    acm=boto3.client("acm", region_name="us-east-1") # NB
    for cert in acm.list_certificates()["CertificateSummaryList"]:
        print ("%s -> %s" % (cert["DomainName"],
                             cert["CertificateArn"]))

