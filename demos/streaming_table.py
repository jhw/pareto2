from pareto2.recipes.streaming_table import StreamingTable

import json, os

if __name__ == "__main__":
    table = StreamingTable(namespace = "app")
    template = table.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/streaming-table.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

