import io, os, unittest, zipfile

class Assets(dict):

    def __init__(self, loader):
        dict.__init__(self, {path: content
                             for path, content in loader})
    
    """
    You can get some weird Lambda errors on execution if you fail to zip the archives properly
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

    def put_s3_zipped(self, s3, bucket_name, file_name):
        s3.put_object(Bucket = bucket_name,
                      Key = file_name,
                      Body = self.zipped_content,
                      ContentType = "application/gzip")

    def put_files(self, root = "tmp"):
        for k, v in self.items():
            dirname="/".join([root]+k.split("/")[:-1])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename=k.split("/")[-1]
            with open("%s/%s" % (dirname, filename), 'w') as f:
                f.write(v)
        
def file_loader(pkg_root,
                root_dir='',
                path_rewriter = lambda x: x,
                filter_fn = lambda x: True):
    pkg_full_path = os.path.join(root_dir, pkg_root)
    for root, dirs, files in os.walk(pkg_full_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            full_path = os.path.join(root, file)
            if filter_fn(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    relative_path = os.path.relpath(full_path, root_dir)
                    yield (path_rewriter(relative_path), content)

def s3_zip_loader(s3, bucket_name, key,
                  path_rewriter = lambda x: x,
                  filter_fn = lambda x: True):
    zf=zipfile.ZipFile(io.BytesIO(s3.get_object(Bucket=bucketname,
                                                Key=key)["Body"].read()))
    for item in zf.infolist():
        if (filterfn(item.filename) and
            not item.filename.endswith("/")):
            content = zf.read(item.filename).decode("utf-8")
            yield (path_rewriter(item.filename), content)
                    
class AssetsTest(unittest.TestCase):
    
    def test_zipped_content(self, pkg_root = "hello"):
        assets = Assets(file_loader(pkg_root))
        buf = assets.zipped_content
        zf = zipfile.ZipFile(io.BytesIO(buf))
        filenames = [item.filename for item in zf.infolist()]
        self.assertTrue(f"{pkg_root}/__init__.py" in filenames)
        self.assertTrue(len(filenames) > 1)
        
if __name__ == "__main__":
    unittest.main()
        
