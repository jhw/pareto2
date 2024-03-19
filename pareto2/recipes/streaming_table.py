from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.dynamodb import *

from pareto2.recipes import Recipe

class StreamingTable(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(SingleStreamingTable(namespace = namespace))
            
if __name__ == "__main__":
    pass

    
