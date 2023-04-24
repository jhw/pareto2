import boto3

if __name__=="__main__":
    acm=boto3.client("acm", region_name="us-east-1") # NB
    for cert in acm.list_certificates()["CertificateSummaryList"]:
        print ("--- %s ---" % (cert["DomainName"]))
        print ("arn: %s" % cert["CertificateArn"])
        cert_=acm.describe_certificate(CertificateArn=cert["CertificateArn"])["Certificate"]
        print ("status: %s" % cert_["Status"])

