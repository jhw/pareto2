from pareto2.api import file_loader
from pareto2.api.tester import Tester

import os

if __name__ == "__main__":
    try:
        pkg_root = os.environ["PKG_ROOT"]
        if pkg_root in ["", None]:
            raise RuntimeError("PKG_ROOT not found")
        os.system(f"rm -rf tmp/{pkg_root}")
        tester = Tester({k:v for k, v in file_loader(pkg_root)})
        tester.dump_assets()
        tester.run_tests()
    except RuntimeError as error:
        print ("Error: %s" % error)
