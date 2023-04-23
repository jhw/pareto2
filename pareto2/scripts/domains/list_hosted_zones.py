import boto3

if __name__=="__main__":
    route53=boto3.client('route53')
    resp=route53.list_hosted_zones()
    for domain in resp['HostedZones']:
        print (domain['Name'])
