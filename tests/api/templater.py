from pareto2.api.assets import file_loader
from pareto2.api.env import Env
from pareto2.api.templater import Templater

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import unittest

PkgRoot = "hello"

@mock_s3
class ApiTemplaterTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_webapi(self,
                    pkg_root = PkgRoot,
                    bucket_name = BucketName,
                    parameters = ['AllowedOrigins',
                                  'ArtifactsBucket',
                                  'ArtifactsKey',
                                  'DomainName',
                                  'RegionalCertificateArn',
                                  'SlackWebhookUrl']):
        templater = Templater(pkg_root = pkg_root,
                              assets = {k:v for k, v in file_loader(pkg_root)})
        env = Env({param: None for param in parameters})
        template = templater.spawn_template(env = env)
        self.assertTrue(template.is_complete)
        template.dump_s3(s3 = self.s3,
                         bucket_name = bucket_name,
                         key = "template.json")
        resp = self.s3.list_objects(Bucket = bucket_name)
        objects = resp["Contents"] if "Contents" in resp else []
        keys = [obj["Key"] for obj in objects]
        self.assertTrue("template.json" in keys)

    def test_website(self,
                     pkg_root = PkgRoot,
                     bucket_name = BucketName,
                     parameters = ['ArtifactsBucket',
                                   'ArtifactsKey',
                                   'DistributionCertificateArn',
                                   'DomainName',
                                   'SlackWebhookUrl']):
        filter_fn = lambda x: "builder" not in x
        templater = Templater(pkg_root = pkg_root,
                              assets = {k:v for k, v in file_loader(pkg_root,
                                                                    filter_fn = filter_fn)})
        root_infra = templater.root_content["infra"]
        for attr in ["api", "builder"]:
            root_infra.pop(attr)
        root_infra.setdefault("bucket", {})
        root_infra["bucket"]["public"] = True
        env = Env({param: None for param in parameters})
        template = templater.spawn_template(env = env)        
        self.assertTrue(template.is_complete)
        template.dump_s3(s3 = self.s3,
                         bucket_name = bucket_name,
                         key = "template.json")
        resp = self.s3.list_objects(Bucket = bucket_name)
        objects = resp["Contents"] if "Contents" in resp else []
        keys = [obj["Key"] for obj in objects]
        self.assertTrue("template.json" in keys)

    def tearDown(self):
        super().tearDown()
        
if __name__ == "__main__":
    unittest.main()
        
