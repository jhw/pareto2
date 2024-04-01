from pareto2.recipes.web_site import WebSite

import unittest

class WebSiteTest(unittest.TestCase):

    def test_template(self):
        template = WebSite(namespace = "app").render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/web-site.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 2)
        for attr in ["DomainName",
                     "CertificateArn"]:
            self.assertTrue(attr in parameters)
        
if __name__ == "__main__":
    unittest.main()
