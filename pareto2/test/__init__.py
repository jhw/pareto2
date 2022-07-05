import boto3, json, unittest, warnings, yaml

from botocore.exceptions import ClientError

import os, yaml

MyBucket=yaml.safe_load("""
name: my-bucket
""")

MyTable=yaml.safe_load("""
indexes: []
name: my-table
stream:
  retries: 3
  batch:
    window: 1
  type: NEW_AND_OLD_IMAGES    
""")

MyRouter=yaml.safe_load("""
name: my-router
patterns: []
""")

FunctionName="my-function"

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
                  tables=[MyTable]):
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
        def create_table(client, resource, table):            
            props=init_table(table)
            client.create_table(**props)
            return resource.Table(table["name"])
        client=boto3.client("dynamodb")
        resource=boto3.resource("dynamodb")
        self.tables=[create_table(client, resource, table)
                     for table in tables]
                
    def teardown_ddb(self):
        for table in self.tables:
            table.delete()

    ### s3

    def setup_s3(self, buckets=[MyBucket]):
        def create_bucket(s3, bucket):
            config={'LocationConstraint': 'EU'}
            s3.create_bucket(Bucket=bucket["name"],
                             CreateBucketConfiguration=config)
        self.s3=boto3.client("s3")
        for bucket in buckets:
            create_bucket(s3, bucket)

    def teardown_s3(self, bucket=[MyBucket]):
        def empty_bucket(s3, bucket):            
            struct=s3.list_objects(Bucket=bucket["name"])
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    s3.delete_object(Bucket=bucket["name"],
                                     Key=obj["Key"])
        def delete_bucket(s3, bucket):
            s3.delete_bucket(Bucket=bucket["name"])
        for bucket in buckets:
            empty_bucket(self.s3, bucket)
            delete_bucket(self.s3, bucket)
                
    ### sqs

    
    def setup_sqs(self, queuenames):
        self.sqs=boto3.client("sqs")
        for queuename in queuenames:
            self.sqs.create_queue(QueueName=queuename)
        
    def list_queues(self):
        def fetch_queue(queueurl):
            queue=self.sqs.get_queue_attributes(QueueUrl=queueurl)["Attributes"]
            queue["QueueName"]=queue["QueueArn"].split(":")[-1]
            queue["QueueUrl"]=queueurl
            return queue        
        return [fetch_queue(queueurl)
                for queueurl in self.sqs.list_queues()["QueueUrls"]]

    def fetch_queue_name(self, queuename):
        queues={queue["QueueName"]:queue
                for queue in self.list_queues()}
        return queues[queuename]
    
    def drain_queue_name(self, queuename):
        queue=self.fetch_queue_name(queuename)
        return self.drain_queue_url(queue["QueueUrl"])
    
    def drain_queue_url(self, queueurl, nmax=100):
        messages, count = [], 0
        while True:
            resp=self.sqs.receive_message(QueueUrl=queueurl)
            if ("Messages" not in resp or
                count > nmax):
                break
            messages+=resp["Messages"]
            count+=1
        return messages

    def teardown_sqs(self):
        queues=self.list_queues()
        for queue in queues:
            self.sqs.delete_queue(QueueUrl=queue["QueueUrl"])

    ### events

    def setup_events(self, routers=[MyRouter]):
        def init_events(events, sqs, router):
            eventbusname="%s-event-bus" % router["name"]
            queuename="%s-target-queue" % router["name"]
            ruleprefix="%s-rule-prefix" % router["name"]        
            events.create_event_bus(Name=eventbusname)
            statement=[{"Effect": "Allow",
                        "Principal": {"Service": "events.amazonaws.com"},
                        "Action": "sqs:SendMessage",
                        "Resource": "*"}]
            policy=json.dumps({"Version": "2012-10-17",
                               "Statement": [statement]})
            queue=sqs.create_queue(QueueName=queuename,
                                   Attributes={"Policy": policy})
            queueattrs=sqs.get_queue_attributes(QueueUrl=queue["QueueUrl"])
            queuearn=queueattrs["Attributes"]["QueueArn"]
            for i, pattern in enumerate(router["patterns"]):
                rulename="%s-%i" % (ruleprefix, i+1)
                ruletargetid="%s-target-%i" % (ruleprefix, i+1)
                events.put_rule(EventBusName=eventbusname,
                                Name=rulename,
                                State="ENABLED",
                                EventPattern=json.dumps(pattern))
                events.put_targets(EventBusName=eventbusname,
                                   Rule=rulename,
                                   Targets=[{"Id": ruletargetid,
                                             "Arn": queuearn}])
        self.events, self.sqs = (boto3.client("events"),
                                 boto3.client("sqs"))
        for router in routers:
            init_events(self.events, self.sqs, router)
                        
    def teardown_events(self,
                        routers=[MyRouter]):
        def delete_events(events, sqs, router, queues):
            eventbusname="%s-event-bus" % router["name"]
            queuename="%s-target-queue" % router["name"]
            for rule in events.list_rules(EventBusName=eventbusname)["Rules"]:
                targets=events.list_targets_by_rule(Rule=rule["Name"])["Targets"]
                for target in targets:
                    events.remove_targets(Rule=rule["Name"],
                                          Ids=[target["Id"]])
                events.delete_rule(Name=rule["Name"])
            queue=queues[queuename]
            self.sqs.delete_queue(QueueUrl=queue["QueueName"])
            events.delete_event_bus(Name=eventbusname)
        queues={queue["QueueName"]: queue
                for queue in self.list_queues()}
        for router in routers:
            delete_events(self.events, self.sqs, router, queues)
            
if __name__=="___main__":
    pass
