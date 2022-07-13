from pareto2.cli import load_config

import importlib, inspect, os, unittest

def filter_tests(root=os.environ["APP_ROOT"]):
    classes=[]
    for parent, _, itemnames in os.walk(root):
        if "__pycache__" in parent:
            continue
        for itemname in itemnames:
            if (not itemname.endswith(".py") or
                itemname=="index.py"):
                continue
            modname="%s.%s" % (parent.replace("/", "."),
                               itemname.split(".")[0])
            mod=importlib.import_module(modname)
            classes+=[obj for name, obj in inspect.getmembers(mod, inspect.isclass)
                      if name.endswith("Test")]
    return classes

def run_tests(tests):
    suite=unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    return runner.run(suite)

if __name__=="__main__":
    classes=filter_tests()
    run_tests(classes)
    
