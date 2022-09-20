import boto3, json, unittest, warnings, yaml

from botocore.exceptions import ClientError

import os, yaml

TestBucket=yaml.safe_load("""
name: test-bucket
""")

TestTable=yaml.safe_load("""
indexes: []
name: test-table
stream:
  retries: 3
  batch:
    window: 1
  type: NEW_AND_OLD_IMAGES    
""")

TestTopic=yaml.safe_load("""
name: test-topic
""")

FunctionName="test-function"

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
                  tables=[TestTable]):
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
            props={"TableName": table["name"],
                   "BillingMode": "PAY_PER_REQUEST",
                   "AttributeDefinitions": attrs,
                   "KeySchema": key}
            if ("indexes" in table and
                table["indexes"]):
                gsi=[{"IndexName": "%s-index" % index["name"],
                      "Projection": {"ProjectionType": "ALL"},
                      "KeySchema": [{"AttributeName": index["name"],
                                     "KeyType": "HASH"}]}
                     for index in table["indexes"]]
                props["GlobalSecondaryIndexes"]=gsi
            return props
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

    def setup_s3(self, buckets=[TestBucket]):
        def create_bucket(s3, bucket):
            config={'LocationConstraint': 'EU'}
            s3.create_bucket(Bucket=bucket["name"],
                             CreateBucketConfiguration=config)
        self.s3=boto3.client("s3")
        for bucket in buckets:
            create_bucket(self.s3, bucket)

    def teardown_s3(self, buckets=[TestBucket]):
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

    # sns

    def setup_sns(self, topics=[TestTopic]):
        self.sns=boto3.client("sns")
        self.topics=[self.sns.create_topic(Name=topic["name"])
                     for topic in topics]

    def teardown_sns(self):
        for topic in self.topics:
            self.sns.delete_topic(TopicArn=topic["TopicArn"])
        
if __name__=="___main__":
    pass
