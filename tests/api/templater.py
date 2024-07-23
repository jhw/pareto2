from pareto2.api import file_loader
from pareto2.api.assets import Assets
from pareto2.api.env import Env
from pareto2.api.templater import Templater

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import unittest

@mock_s3
class ApiTemplaterTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_hello(self,
                    app_name = "hello",
                    pkg_root = "hello",
                    bucket_name = BucketName):
        path_rewriter = lambda x: "/".join(x.split("/")[1:])
        assets = Assets({k:v for k, v in file_loader(app_name, # include setenv.sh
                                                     path_rewriter = path_rewriter)})
        templater = Templater(pkg_root = pkg_root,
                              assets = assets)
        env = Env.create_from_bash(assets["setenv.sh"])
        env.update({attr:None for attr in ["ArtifactsKey",
                                           "RegionalCertificateArn"]})
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
        
