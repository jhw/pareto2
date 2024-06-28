import os, unittest, warnings

from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

def find_and_run_tests(root_dirs):
    suite = unittest.TestSuite()    
    for root_dir in root_dirs:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    module_name = full_path.replace(os.sep, '.')[:-3] 
                    module = __import__(module_name, fromlist=[''])
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (isinstance(obj, type) and
                            issubclass(obj, unittest.TestCase) and
                            "Base" not in str(obj)):
                            print (str(obj)[1:-1].split(" ")[-1][1:-1])
                            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(obj))
    unittest.TextTestRunner().run(suite)

if __name__ == "__main__":
    os.system("sudo rm -rf /tmp/*") # clean local filesystem
    find_and_run_tests(["tests"])
