from pareto2.ingredients import hungarorise as H

from pareto2.ingredients.sqs import Queue

from pareto2.recipes import Recipe

import importlib

task_queue_module = importlib.import_module("pareto2.ingredients.lambda.task_queue")

class TaskQueue(Recipe):    

    def __init__(self,
                 namespace):
        super().__init__()
        self.append(Queue(namespace = namespace))
        self.init_streaming(parent_ns = namespace)        

    def init_streaming(self, parent_ns):
        child_ns = f"{parent_ns}-task-queue"        
        for attr in ["TaskQueueFunction",
                     "TaskQueueRole",
                     "TaskQueuePolicy",
                     "TaskQueueEventSourceMapping"]:
            fn = getattr(task_queue_module, attr)
            self.append(fn(namespace = child_ns,
                           queue_namespace = parent_ns))
            
if __name__ == "__main__":
    pass

    
