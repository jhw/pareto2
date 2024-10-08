import boto3
import re
import sys
import time

def list_hosted_zones(route53):
    print("fetching hosted zones")
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_record_sets(route53, hosted_zone_id):
    print(f"fetching record sets for {hosted_zone_id}")
    return route53.list_resource_record_sets(HostedZoneId = hosted_zone_id)["ResourceRecordSets"]

def list_certificates(acm):
    print("fetching certificates")
    return {cert["DomainName"]:cert["CertificateArn"]
            for cert in acm.list_certificates()["CertificateSummaryList"]}

def fetch_resource_record(acm, cert_arn, max_tries = 30, wait = 2):
    for i in range(max_tries):
        print(f"fetching resource record for {cert_arn} [{i+1}/{max_tries}]")
        cert = acm.describe_certificate(CertificateArn = resp["CertificateArn"])["Certificate"]
        if ("DomainValidationOptions" in cert and
            cert["DomainValidationOptions"] != [] and
            "ResourceRecord" in cert["DomainValidationOptions"][0]):
            return cert["DomainValidationOptions"][0]["ResourceRecord"]
        time.sleep(wait)
    raise RuntimeError(f"no resource record found for {cert_arn}")

def check_certificate_status(acm, cert_arn, max_tries = 500, wait = 2, target_status = "ISSUED"):
    for i in range(max_tries):
        cert = acm.describe_certificate(CertificateArn = cert_arn)["Certificate"]
        print(f"certificate status {cert['Status']} [{i+1}/{max_tries}]")
        if cert["Status"] == target_status:
            return
        time.sleep(wait)
    raise RuntimeError(f"certificate status of {target_status} not realised")

if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter host_name, region")
        host_name, region = sys.argv[1:3]
        nperiods = len([c for c in host_name
                        if c == "."])
        if nperiods != 1:            
            raise RuntimeError("host_name can only have a single period")
        if host_name[-1] == ".":
            raise RuntimeError("host_name cannot end in period")
        if not re.search("^\\D{2}\\-\\D{4}\\-\\d{1}$", region):
            raise RuntimeError("region is invalid")
        route53 = boto3.client("route53")
        hosted_zones = list_hosted_zones(route53)
        hosted_zone_name = f"{host_name}."
        if hosted_zone_name not in hosted_zones:
            raise RuntimeError(f"hosted zone {hosted_zone_name} not found")
        hosted_zone_id = hosted_zones[hosted_zone_name]
        record_sets = list_record_sets(route53, hosted_zone_id)
        record_settypes = set([record_set["Type"] for record_set in record_sets])
        """
        if "CNAME" in record_set_types:
            raise RuntimeError("CNAME already exists in hosted zone %s" % hosted_zone_name)
        """
        acm = boto3.client("acm", region_name = region)
        certificates = list_certificates(acm)
        cert_domain_name = f"*.{host_name}"
        if cert_domain_name in certificates:
            raise RuntimeError(f"cert {cert_domain_name} already exists")
        print(f"fetching certificate for {cert_domain_name}")
        resp = acm.request_certificate(DomainName = cert_domain_name,
                                       ValidationMethod = "DNS",
                                       SubjectAlternativeNames = [cert_domain_name])
        cert_arn = resp["CertificateArn"]
        resource_record = fetch_resource_record(acm, cert_arn)
        resource_record_set = {"Name": resource_record["Name"],
                               "Type": "CNAME",
                               "TTL": 300,
                               "ResourceRecords": [{"Value": resource_record["Value"]}]}
        change_batch = {"Changes": [{'Action': 'UPSERT',
                                     'ResourceRecordSet': resource_record_set}]}
        print(f"creating CNAME record for {hosted_zone_id}")
        print(route53.change_resource_record_sets(HostedZoneId = hosted_zone_id,
                                                   ChangeBatch = change_batch))
        print("checking certificate status")
        check_certificate_status(acm, cert_arn)
    except RuntimeError as error:
        print(f"Error: {error}")
