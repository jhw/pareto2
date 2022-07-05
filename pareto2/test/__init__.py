import boto3, json, unittest, warnings, yaml

from botocore.exceptions import ClientError

import os, yaml

BucketName="my-bucket"

TableName="my-table"

RouterName="my-router"

FunctionName="my-function"

TableConfig=yaml.safe_load("""
indexes: []
name: my-table
stream:
  retries: 3
  batch:
    window: 1
  type: NEW_AND_OLD_IMAGES    
""")

class Context:

    def __init__(self, functionname=FunctionName):
        self.function_name=functionname

class Pareto2TestBase(unittest.TestCase):

    """
    - https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file
    - https://stackoverflow.com/a/63902279/124179
    - https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
    """
    
    @classmethod
    def setUpClass(cls):
        def init_stdout_logger():
            import logging, sys
            logger=logging.getLogger()
            if not logger.handlers:
                logger.setLevel(logging.INFO)    
                sh=logging.StreamHandler(sys.stdout)
                formatter=logging.Formatter('[%(levelname)s] %(message)s')
                sh.setFormatter(formatter)
                logger.addHandler(sh)
        init_stdout_logger()
        warnings.simplefilter("ignore")

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.env={}

    ### dynamodb
        
    def setup_ddb(self,
                  table=TableConfig):
        def init_table(table):
            attrs=[{"AttributeName": name,
                    "AttributeType": type_}
                   for name, type_ in [("pk", "S"),
                                       ("sk", "S")]+[(index["name"], index["type"])
                                                     for index in table["indexes"]]]
            key=[{"AttributeName": k,
                  "KeyType": v}
                 for k, v in [("pk", "HASH"),
                              ("sk", "RANGE")]]
            gsi=[{"IndexName": "%s-index" % index["name"],
                  "Projection": {"ProjectionType": "ALL"},
                  "KeySchema": [{"AttributeName": index["name"],
                                 "KeyType": "HASH"}]}
                 for index in table["indexes"]]
            return {"TableName": table["name"],
                    "AttributeDefinitions": attrs,
                    "KeySchema": key,
                    "GlobalSecondaryIndexes": gsi}
        client=boto3.client("dynamodb")
        props=init_table(table)
        client.create_table(**props)
        resource=boto3.resource("dynamodb")
        self.table=resource.Table(table["name"])
        
    def teardown_ddb(self):
        self.table.delete()

    ### s3

    def setup_s3(self, bucketnames=[BucketName]):
        def create_bucket(s3, bucketname):
            config={'LocationConstraint': 'EU'}
            s3.create_bucket(Bucket=bucketname,
                                  CreateBucketConfiguration=config)
        self.s3=boto3.client("s3")
        for bucketname in bucketnames:
            create_bucket(s3, bucketname)

    def teardown_s3(self, bucketnames=[BucketName]):
        def empty_bucket(s3, bucketname):            
            struct=s3.list_objects(Bucket=bucketname)
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    s3.delete_object(Bucket=bucketname,
                                          Key=obj["Key"])
        def delete_bucket(s3, bucketname):
            s3.delete_bucket(Bucket=bucketname)
        for bucketname in bucketnames:
            empty_bucket(self.s3, bucketname)
            delete_bucket(self.s3, bucketname)
                
    ### sqs

    def setup_sqs(self, queuenames):
        self.sqs=boto3.client("sqs")
        self.queues={queuename: self.sqs.create_queue(QueueName=queuename)
                     for queuename in queuenames}            

    def drain_sqs(self, queueurl, nmax=100):
        messages, count = [], 0
        while True:
            resp=self.sqs.receive_message(QueueUrl=queueurl)
            if ("Messages" not in resp or
                count > nmax):
                break
            messages+=resp["Messages"]
            count+=1
        return messages

    def teardown_sqs(self, queuenames):
        for queuename in queuenames:
            queue=self.queues[queuename]
            self.sqs.delete_queue(QueueUrl=queue["QueueUrl"])

    ### events

    def setup_events(self, patterns=[],
                     routername=RouterName):
        eventbusname="%s-event-bus" % routername
        queuename="%s-queue" % routername
        ruleprefix="%s-rule-prefix" % routername        
        self.patterns=patterns
        self.events, self.sqs = (boto3.client("events"),
                                 boto3.client("sqs"))
        self.events.create_event_bus(Name=eventbusname)
        statement=[{"Effect": "Allow",
                    "Principal": {"Service": "events.amazonaws.com"},
                    "Action": "sqs:SendMessage",
                    "Resource": "*"}]
        policy=json.dumps({"Version": "2012-10-17",
                           "Statement": [statement]})
        queue=self.sqs.create_queue(QueueName=queuename,
                                    Attributes={"Policy": policy})
        self.eventqueueurl=queue["QueueUrl"]
        queueattrs=self.sqs.get_queue_attributes(QueueUrl=self.eventqueueurl)
        queuearn=queueattrs["Attributes"]["QueueArn"]
        for i, pattern in enumerate(patterns):
            rulename="%s-%i" % (ruleprefix, i+1)
            ruletargetid="%s-target-%i" % (ruleprefix, i+1)
            self.events.put_rule(EventBusName=eventbusname,
                                 Name=rulename,
                                 State="ENABLED",
                                 EventPattern=json.dumps(pattern))
            self.events.put_targets(EventBusName=eventbusname,
                                    Rule=rulename,
                                    Targets=[{"Id": ruletargetid,
                                              "Arn": queuearn}])        

    def teardown_events(self,
                        routername=RouterName):
        eventbusname="%s-event-bus" % routername
        ruleprefix="%s-rule-prefix" % routername        
        for i, pattern in enumerate(self.patterns):
            rulename="%s-%i" % (ruleprefix, i+1)  
            ruletargetid="%s-target-%i" % (ruleprefix, i+1)
            self.events.remove_targets(Rule=rulename,
                                       Ids=[ruletargetid])
            self.events.delete_rule(Name=rulename)
        self.sqs.delete_queue(QueueUrl=self.eventqueueurl)
        self.events.delete_event_bus(Name=eventbusname)
            
if __name__=="___main__":
    pass
