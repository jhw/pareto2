from pareto2.recipes.event_worker import EventWorker

import json, os, yaml

Worker = yaml.safe_load("""
  permissions:
  - s3:GetObject
""")

CodeBody="""
def handler(event, context=None):
    print (event)
"""

if __name__ == "__main__":
    _worker = Worker
    _worker["code"] = CodeBody
    worker = EventWorker(namespace = "my",
                         worker = _worker)
    template = worker.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/event-worker.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

