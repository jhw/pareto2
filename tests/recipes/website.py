from pareto2.recipes.website import Website

import unittest

class WebsiteDemoTest(unittest.TestCase):

    def test_template(self):
        recipe = Website(namespace = "app")
        template = recipe.render()
        template.init_parameters()
        template.dump_file(filename = "tmp/website.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 2)
        for attr in ["DomainName",
                     "DistributionCertificateArn"]:
            self.assertTrue(attr in parameters)
        
if __name__ == "__main__":
    unittest.main()
