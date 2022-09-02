from pareto2.core.components import hungarorise

import yaml

def load_config(filename="config.yaml"):
    return yaml.safe_load(open(filename).read())

if __name__=="__main__":
    pass

