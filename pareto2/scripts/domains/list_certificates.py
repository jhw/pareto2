import boto3
import re
import sys

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter region")
        region = sys.argv[1]
        if not re.search("^\\D{2}\\-\\D{4}\\-\\d{1}$", region):
            raise RuntimeError("region is invalid")
        acm = boto3.client("acm", region_name = region) # NB
        for cert in acm.list_certificates()["CertificateSummaryList"]:
            print(f"--- {cert['DomainName']} ---")
            print(f"arn: {cert['CertificateArn']}")
            cert_ = acm.describe_certificate(CertificateArn = cert["CertificateArn"])["Certificate"]
            print(f"status: {cert_['Status']}")
    except RuntimeError as error:
        print(f"Error: {error}")
