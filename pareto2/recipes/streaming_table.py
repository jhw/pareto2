from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.dynamodb import *

from pareto2.recipes import Recipe

import importlib

sst_module = importlib.import_module("pareto2.ingredients.lambda.single_streaming_table")

class StreamingTable(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(SingleStreamingTable(namespace = namespace))
        self.init_streaming(parent_ns = namespace)        

    def init_streaming(self, parent_ns):
        child_ns = f"{parent_ns}-streaming-table"        
        for fn in [sst_module.SingleStreamingTableFunction,
                   sst_module.SingleStreamingTableRole,
                   sst_module.SingleStreamingTableEventSourceMapping]:
            self.append(fn(namespace = child_ns,
                           table_namespace = parent_ns))
            
if __name__ == "__main__":
    pass

    
