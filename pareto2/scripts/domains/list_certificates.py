import boto3, re, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter region")
        region=sys.argv[1]
        if not re.search("^\\D{2}\\-\\D{4}\\-\\d{1}$", region):
            raise RuntimeError("region is invalid")
        acm=boto3.client("acm", region_name=region) # NB
        for cert in acm.list_certificates()["CertificateSummaryList"]:
            print ("--- %s ---" % (cert["DomainName"]))
            print ("arn: %s" % cert["CertificateArn"])
            cert_=acm.describe_certificate(CertificateArn=cert["CertificateArn"])["Certificate"]
            print ("status: %s" % cert_["Status"])
    except RuntimeError as error:
        print ("Error: %s" % str(error))
