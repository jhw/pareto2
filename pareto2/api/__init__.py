import io
import os
import zipfile

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
