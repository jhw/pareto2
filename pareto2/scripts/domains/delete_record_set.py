import boto3, sys

def list_hosted_zones(route53):
    return {zone["Name"]: zone["Id"]
            for zone in (route53.list_hosted_zones_by_name()["HostedZones"])}

def list_record_sets(route53, hostedzoneid):
    return route53.list_resource_record_sets(HostedZoneId=hostedzoneid)["ResourceRecordSets"]

"""
https://stackoverflow.com/questions/40196558/aws-python-sdk-route-53-delete-resource-record
"""

if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter hostname, record set name")
        hostname, recordsettype = sys.argv[1:3]
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
        recordsets=list_record_sets(route53, hostedzoneid)
        recordsettypes=[recordset["Type"] for recordset in recordsets]
        if recordsettype not in set(recordsettypes):
            raise RuntimeError("%s record set not found in hosted zone %s" % (recordsettype, hostedzonename))
        matchingrecordsets=[recordset for recordset in recordsets
                            if recordset["Type"]==recordsettype]
        if len(matchingrecordsets)!=1:
            raise RuntimeError("multiple %s record sets in hosted zone %s" % (recordsettype, hostedzonename))
        recordset=matchingrecordsets[0]
        recordset.pop("ResourceRecords")
        changebatch={"Changes": [{'Action': 'DELETE',
                                  'ResourceRecordSet': recordset}]}
        """
        print (route53.change_resource_record_set(HostedZoneId=hostedzoneid,
                                                  ChangeBatch=changebatch))
        """
    except RuntimeError as error:
        print ("Error: %s" % str(error))
