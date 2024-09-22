import boto3

if __name__ == "__main__":
    route53 = boto3.client('route53')
    resp = route53.list_hosted_zones()
    for domain in resp['HostedZones']:
        print("--- %s ---" % domain['Name'])
        records = route53.list_resource_record_sets(HostedZoneId = domain['Id'])
        for record in records['ResourceRecordSets']:
            print(f"{record['Name']} [{record['Type']}]")
