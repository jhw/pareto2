import io, os, zipfile

class Assets(dict):

    def __init__(self, item = {}):
        dict.__init__(self, item)
    
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
                    
if __name__ == "__main__":
    pass
