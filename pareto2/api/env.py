from pareto2.services import hungarorise as H

import os

class Env(dict):

    @classmethod
    def create_from_os_environ(self):
        return Env({H(k):v for k, v in os.environ.items()})

    @classmethod
    def create_from_bash(self, text):
        def init_tuple(kv):
            return (H(kv[0]), kv[1])
        return Env(dict([init_tuple([tok.replace('"', "")
                                     for tok in row.split(" ")[1].split("=")])
                         for row in text.split("\n")
                         if row.replace(" ", "").lower().startswith("export")]))
    
    def __init__(self, item = {}):
        dict.__init__(self, item)

    def update_layers(self, L):
        pass

    def update_certificates(self, L):
        pass
