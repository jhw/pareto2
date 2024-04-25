from pareto2.api import file_loader
from pareto2.api.env import Env
from pareto2.api.tester import Tester

import os

if __name__ == "__main__":
    try:
        env = Env.create_from_environ()
        if "PkgRoot" not in env:
            raise RuntimeError("env is missing PKG_ROOT")
        pkg_root = env["PkgRoot"]
        os.system(f"rm -rf tmp/{pkg_root}")
        tester = Tester({k:v for k, v in file_loader(pkg_root)})
        tester.dump_assets(root = "tmp")
        tester.run_tests(root = "tmp")
    except RuntimeError as error:
        print ("Error: %s" % error)
