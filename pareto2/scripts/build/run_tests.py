import importlib, inspect, os, unittest
        
def filter_tests(root):
    tests=[]
    for localroot, dirs, files in os.walk(root):
        for filename in files:
            if filename=="test.py":
                absfilename=os.path.join(localroot, filename)
                modname=absfilename.split(".")[0].replace("/", ".")
                mod=importlib.import_module(modname)
                tests+=[obj for name, obj in inspect.getmembers(mod,
                                                                inspect.isclass)
                        if name.endswith("Test")]
    return tests

def run_tests(tests):
    suite=unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    result=runner.run(suite)
    if (result.errors!=[] or
        result.failures!=[]):
        raise RuntimeError("/n".join([error[1]
                                      for error in result.errors+result.failures]))

if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("app package not found")
        tests=filter_tests(appname.replace("-", ""))
        run_tests(tests)
    except RuntimeError as error:
        print ("Error: %s" % error)


