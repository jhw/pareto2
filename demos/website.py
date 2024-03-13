from pareto2.recipes.website import Website

import json, os

if __name__ == "__main__":
    site = Website(namespace = "app")
    template = site.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/website.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

