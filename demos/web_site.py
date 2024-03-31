from pareto2.recipes.web_site import WebSite

if __name__ == "__main__":
    template = WebSite(namespace = "app").render()
    template.populate_parameters()
    template.dump_file(filename = "tmp/web-site.json")
    print (", ".join(list(template["Parameters"].keys())))
