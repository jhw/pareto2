from pareto2.api import file_loader
from pareto2.api.env import Env
from pareto2.api.tester import Tester

import os

"""
Note call to clean local /tmp filesystem, to avoid cross- pollution by different projects

On Lambda the container is brought down each time in `finally` block; a new container starts with a clean /tmp
"""

if __name__ == "__main__":
    try:
        env = Env.create_from_environ()
        if "PkgRoot" not in env:
            raise RuntimeError("env is missing PKG_ROOT")
        pkg_root = env["PkgRoot"]
        if os.path.exists("/tmp"):
            os.system("rm -rf /tmp/*") # NB 
        tester = Tester({k:v for k, v in file_loader(pkg_root)})
        tester.dump_assets()
        tester.run_tests()
    except RuntimeError as error:
        print ("Error: %s" % error)
