from pareto2.recipes.pip_builder import PipBuilder

import json, os

if __name__ == "__main__":
    recipe = PipBuilder(namespace = "app")
    template = recipe.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/pip-builder.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))
    print (", ".join(list(template["Parameters"].keys())))
