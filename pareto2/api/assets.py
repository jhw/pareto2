import io, os, zipfile

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

    def dump_s3(self, s3, bucket_name, key):
        s3.put_object(Bucket = bucket_name,
                      Key = key,
                      Body = self.zipped_content,
                      ContentType = "application/gzip")
        
    def dump_files(self, root = "tmp"):
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
    zf=zipfile.ZipFile(io.BytesIO(s3.get_object(Bucket=bucket_name,
                                                Key=key)["Body"].read()))
    for item in zf.infolist():
        if (filter_fn(item.filename) and
            not item.filename.endswith("/")):
            content = zf.read(item.filename).decode("utf-8")
            yield (path_rewriter(item.filename), content)
                    
if __name__ == "__main__":
    pass
