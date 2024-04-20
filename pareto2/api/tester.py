from pareto2.api.assets import Assets

class Tester(Assets):

    """
    Refs to __file__ in code bodies have to be rewritten since they won't work in the local filesystem
    """

    def __init__(self, item = {}, root = "tmp"):
        super().__init__({k:v.replace("__file__", f"\"{root}/{k}\"")
                          for k, v in item.items()})

if __name__ == "__main__":
    pass
