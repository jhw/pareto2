from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import os, json

def load_files(root):
    roottokens, items = root.split("/"), []
    for localroot, dirs, files in os.walk(root):
        for _filename in files:
            filename=os.path.join(localroot, _filename)
            body=open(filename).read()
            key="/".join(filename.split("/")[len(roottokens)-1:])
            item=(key, body)
            items.append(item)
    return items
    
if __name__=="__main__":    
    try:
        dsl=DSL()
        scripts=Scripts.initialise(load_files("demo/hello"))
        dsl.expand(scripts)
        # print (dsl.formatted)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        with open("tmp/template.json", 'w') as f:
            f.write(json.dumps(template.render(),                               
                               indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
