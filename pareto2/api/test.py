from pareto2.api import Project

from pareto2.api.utils import file_loader

import unittest

class TemplateTest(unittest.TestCase):
    
    def init_filter(self, pkg_root):
        def filter_fn(full_path):
            return (full_path == f"{pkg_root}/__init__.py" or
                    full_path.endswith("index.py"))
        return filter_fn
    
    def init_project(self, pkg_root = "hello"):
        filter_fn = self.init_filter(pkg_root)        
        loader = file_loader(pkg_root,
                             filter_fn = filter_fn)        
        return Project(pkg_root, loader)
    
    def test_webapi(self, required = ['AllowedOrigins',
                                      'ArtifactsBucket',
                                      'ArtifactsKey',
                                      'DomainName',
                                      'RegionalCertificateArn',
                                      'SlackWebhookUrl']):
        project = self.init_project()
        template = project.spawn_template()
        template.dump_file("tmp/hello-webapi.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == len(required))
        for param in required:
            self.assertTrue(param in parameters)

    def test_website(self, required = ['ArtifactsBucket',
                                       'ArtifactsKey',
                                       'DistributionCertificateArn',
                                       'DomainName',
                                       'SlackWebhookUrl']):
        project = self.init_project()
        root_infra = project.root_content["infra"]
        for attr in ["api", "builder"]:
            root_infra.pop(attr)
        root_infra.setdefault("bucket", {})
        root_infra["bucket"]["public"] = True
        template = project.spawn_template()
        template.dump_file("tmp/hello-website.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == len(required))
        for param in required:
            self.assertTrue(param in parameters)

if __name__ == "__main__":
    unittest.main()
