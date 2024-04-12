import os, unittest

def find_and_run_tests(root_dirs):
    suite = unittest.TestSuite()    
    for root_dir in root_dirs:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    module_name = full_path.replace(os.sep, '.')[:-3] 
                    try:
                        module = __import__(module_name, fromlist=[''])
                    except ImportError:
                        continue 
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (isinstance(obj, type) and
                            issubclass(obj, unittest.TestCase)):
                            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(obj))
    unittest.TextTestRunner().run(suite)

if __name__ == "__main__":
    find_and_run_tests(["tests"])
