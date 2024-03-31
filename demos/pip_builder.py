from pareto2.recipes.pip_builder import PipBuilder

if __name__ == "__main__":
    recipe = PipBuilder(namespace = "app")
    template = recipe.render()
    template.populate_parameters()
    template.dump_file(filename = "tmp/pip-builder.json")
    print (", ".join(list(template["Parameters"].keys())))
