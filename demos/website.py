from pareto2.recipes.website import Website

import json

if __name__ == "__main__":
    site = Website(namespace = "my")
    template = site.render()
    template.populate_parameters()
    print (json.dumps(template,
                      indent = 2))

