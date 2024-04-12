from pareto2.services import hungarorise as H

import os

class Env(dict):

    @classmethod
    def create_from_os_environ(self):
        return Env({H(k): v for k, v in os.environ.items()})

    @classmethod
    def create_from_bash(self, text):
        return Env()
    
    def __init__(self, item = {}):
        dict.__init__(self, item)

    def update_layers(self, L):
        pass

    def update_certificates(self, L):
        pass
