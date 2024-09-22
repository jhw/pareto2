import boto3
import re
import sys

def list_hosted_zones(route53):
    print("fetching hosted zones")
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_certificates(acm):
    print("fetching certificates")
    return {cert["DomainName"]:cert["CertificateArn"]
            for cert in acm.list_certificates()["CertificateSummaryList"]}

def list_record_sets(route53, hosted_zone_id):
    print(f"fetching record sets for {hosted_zone_id}")
    return route53.list_resource_record_sets(HostedZoneId = hosted_zone_id)["ResourceRecordSets"]

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
        acm = boto3.client("acm", region_name = region)
        certificates = list_certificates(acm)
        cert_name = f"*.{host_name}"
        if cert_name not in certificates:
            raise RuntimeError(f"cert {cert_name} does not exists")
        cert_arn = certificates[cert_name]
        print(f"deleting certificate {cert_arn}")
        print(acm.delete_certificate(CertificateArn = cert_arn))
        record_sets = list_record_sets(route53, hosted_zone_id)
        record_set_types = [record_set["Type"] for record_set in record_sets]
        record_set_type = "CNAME"
        if record_set_type not in set(record_set_types):
            raise RuntimeError(f"{record_set_type} record set not found in hosted zone {hosted_zone_name}")
        matching_record_sets = [record_set for record_set in record_sets
                                if record_set["Type"] == record_set_type]
        if len(matching_record_sets) != 1:
            raise RuntimeError(f"multiple {record_set_type} record sets in hosted zone {hosted_zone_name}")
        record_set = matching_record_sets[0]
        change_batch = {"Changes": [{'Action': 'DELETE',
                                    'ResourceRecordSet': record_set}]}
        print(f"deleting CNAME record for {hosted_zone_id}"
        print(route53.change_resource_record_sets(HostedZoneId = hosted_zone_id,
                                                  ChangeBatch = change_batch))
    except RuntimeError as error:
        print(f"Error: {error}")
