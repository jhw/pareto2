import boto3, json, math, os

class Key:

    def __init__(self, pk, sk, eventname):
        self.pk = pk
        self.sk = sk
        self.eventname = eventname

    def __str__(self):
        return "%s/%s/%s" % (self.pk,
                             self.sk,
                             self.eventname)

"""
- EventBridge required fields are Source, DetailType, Detail
- record["eventName"] is used as DetailType
- eventName could be INSERT, MODIFY, DELETE
"""
    
class Entry:

    def __init__(self, key, records, source):
        self.key = key
        self.records = records
        self.source = source

    @property
    def entry(self):        
        detail = {"pk": self.key.pk,
                  "sk": self.key.sk,
                  "eventName": self.key.eventname,
                  "records": self.records}
        detailtype = self.key.eventname
        return {"Source": self.source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail)}

def batch_records(records):
    keys, groups  =  {}, {}
    for record in records:
        pk = record["dynamodb"]["Keys"]["pk"]["S"]
        sk = record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        eventname = record["eventName"]
        key = Key(pk = pk,
                  sk = sk,
                  eventname = eventname)
        strkey = str(key)
        if strkey not in keys:
            keys[strkey] = key
        groups.setdefault(strkey, [])
        groups[strkey].append(record)
    return [(key, groups[strkey])
            for strkey, key in keys.items()]

"""
- EventBridge max batch size is 10
"""

def handler(event, context, batchsize = 10):
    source = os.environ["TABLE_NAME"]
    batchsize = int(batchsize)
    events = boto3.client("events")
    groups = batch_records(event["Records"])
    entries = [Entry(k, v, source).entry
               for k, v in groups]
    if entries != []:
        nbatches = math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch = entries[i*batchsize: (i+1)*batchsize]
            events.put_events(Entries = batch)

