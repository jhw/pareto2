from pareto2.recipes.event_worker import EventWorker

import json, os

if __name__ == "__main__":
    worker = EventWorker(namespace = "my")
    template = worker.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/event-worker.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

