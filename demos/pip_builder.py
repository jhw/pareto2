from pareto2.recipes.pip_builder import PipBuilder

import unittest

class PipBuilderTest(unittest.TestCase):

    def test_template(self):
        recipe = PipBuilder(namespace = "app")
        template = recipe.render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/pip-builder.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(parameters == [])

if __name__ == "__main__":
    unittest.main()
