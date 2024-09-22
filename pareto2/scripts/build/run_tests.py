from pareto2.api import file_loader
from pareto2.api.env import Env
from pareto2.api.tester import Tester

import os
import sys

"""
Note call to clean local /tmp filesystem, to avoid cross- pollution by different projects

On Lambda the container is brought down each time in `finally` block; a new container starts with a clean /tmp
"""

if __name__ == "__main__":
    try:
        os.environ["TMP_ROOT"] = tmp_root = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
        if os.path.exists(tmp_root):
            os.system(f"rm -rf {tmp_root}/*")
        env = Env.create_from_environ()
        if "PkgRoot" not in env:
            raise RuntimeError("env is missing PKG_ROOT")
        pkg_root = env["PkgRoot"]
        tester = Tester(item = {k:v for k, v in file_loader(pkg_root)},
                        root = tmp_root)
        tester.dump_assets()
        tester.run_tests()
    except RuntimeError as error:
        print(f"Error: {error}")
