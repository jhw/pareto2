from pareto2.api.assets import file_loader
from pareto2.api.env import Env
from pareto2.api.project import Project

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import unittest

PkgRoot = "hello"

@mock_s3
class ProjectTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def init_filter(self, pkg_root):
        def filter_fn(full_path):
            return (full_path == f"{pkg_root}/__init__.py" or
                    full_path.endswith("index.py"))
        return filter_fn
    
    def init_project(self, pkg_root):
        filter_fn = self.init_filter(pkg_root)
        loader = file_loader(pkg_root,
                             filter_fn = filter_fn)        
        return Project(pkg_root, {k:v for k, v in loader})
    
    def test_webapi(self,
                    pkg_root = PkgRoot,
                    bucket_name = BucketName,
                    parameters = ['AllowedOrigins',
                                  'ArtifactsBucket',
                                  'ArtifactsKey',
                                  'DomainName',
                                  'RegionalCertificateArn',
                                  'SlackWebhookUrl']):
        project = self.init_project(pkg_root = pkg_root)
        env = Env({param: None for param in parameters})
        template = project.spawn_template(env = env)
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
        project = self.init_project(pkg_root = pkg_root)
        root_infra = project.root_content["infra"]
        for attr in ["api", "builder"]:
            root_infra.pop(attr)
        root_infra.setdefault("bucket", {})
        root_infra["bucket"]["public"] = True
        env = Env({param: None for param in parameters})
        template = project.spawn_template(env = env)        
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
        
