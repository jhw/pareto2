from pareto2.recipes.web_site import WebSite

import json, os

if __name__ == "__main__":
    template = WebSite(namespace = "app").render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/web-site.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

