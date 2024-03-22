from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.dynamodb import StreamingTable as StreamingTableResource

from pareto2.recipes import Recipe

import importlib

streaming_table_module = importlib.import_module("pareto2.ingredients.lambda.streaming_table")

class StreamingTable(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(StreamingTableResource(namespace = namespace))
        self.init_streaming(parent_ns = namespace)        

    def init_streaming(self, parent_ns):
        child_ns = f"{parent_ns}-streaming-table"        
        for attr in ["StreamingTableFunction",
                     "StreamingTableRole",
                     "StreamingTablePolicy",
                     "StreamingTableEventSourceMapping"]:
            fn = getattr(streaming_table_module, attr)
            self.append(fn(namespace = child_ns,
                           table_namespace = parent_ns))
            
if __name__ == "__main__":
    pass

    
