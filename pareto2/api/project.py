import io, unittest, zipfile

class Project(dict):

    def __init__(self, pkg_root, loader):
        dict.__init__(self, {path: content
                             for path, content in loader})
        self.pkg_root = pkg_root
    
    """
    You can get some weird Lambda errors on execution if you fail to zip the archives properly
    Unfortunately the chatgpt chat in which this was explained has now been deleted :(
    """
        
    @property
    def zipped_content(self):
        buf = io.BytesIO()
        zf = zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False)
        for k, v in self.items():
            # zf.writestr(k, v)
            unix_mode = 0o100644  # File permission: rw-r--r--
            zip_info = zipfile.ZipInfo(k)
            zip_info.external_attr = (unix_mode << 16) | 0o755  # Add execute permission
            zf.writestr(zip_info, v)
        zf.close()
        return buf.getvalue()

    def put_s3(self, s3, bucket_name, file_name):
        s3.put_object(Bucket = bucket_name,
                      Key = file_name,
                      Body = self.zipped_content,
                      ContentType = "application/gzip")

class ProjectTest(unittest.TestCase):
    
    def init_project(self, pkg_root):
        from pareto2.api import file_loader
        loader = file_loader(pkg_root)
        return Project(pkg_root, loader)
    
    def test_zipped_content(self, pkg_root = "hello"):
        project = self.init_project(pkg_root = pkg_root)
        buf = project.zipped_content
        zf = zipfile.ZipFile(io.BytesIO(buf))
        filenames = [item.filename for item in zf.infolist()]
        self.assertTrue(f"{pkg_root}/__init__.py" in filenames)
        self.assertTrue(len(filenames) > 1)
        
if __name__ == "__main__":
    unittest.main()
        
