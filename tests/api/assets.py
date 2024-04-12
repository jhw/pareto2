from pareto2.api.assets import Assets, file_loader

from tests.api import ApiTestBase, BucketName

import io, unittest, zipfile

PkgRoot = "hello"

class AssetsTest(ApiTestBase):

    def test_zipped_content(self, pkg_root = PkgRoot):
        assets = Assets(file_loader(pkg_root))
        buf = assets.zipped_content
        zf = zipfile.ZipFile(io.BytesIO(buf))
        filenames = [item.filename for item in zf.infolist()]
        self.assertTrue(f"{pkg_root}/__init__.py" in filenames)
        self.assertTrue(len(filenames) > 1)

if __name__ == "__main__":
    unittest.main()
