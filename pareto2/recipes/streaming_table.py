from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.dynamodb import *

from pareto2.recipes import Recipe

import importlib

sst_module = importlib.import_module("pareto2.ingredients.lambda.single_streaming_table")

class StreamingTable(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        child_ns = f"{namespace}-streaming-table"
        self.append(SingleStreamingTable(namespace = namespace))
        self.append(sst_module.SingleStreamingTableFunction(namespace = child_ns,
                                                            table_namespace = namespace))
        self.append(sst_module.SingleStreamingTableRole(namespace = child_ns,
                                                        table_namespace = namespace))
        self.append(sst_module.SingleStreamingTableEventSourceMapping(namespace = child_ns,
                                                                      table_namespace = namespace))
            
if __name__ == "__main__":
    pass

    
