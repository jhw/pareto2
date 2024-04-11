import os

def file_loader(pkg_root, root_dir='', filter_fn = lambda x: True):
    pkg_full_path = os.path.join(root_dir, pkg_root.replace("-", ""))
    for root, dirs, files in os.walk(pkg_full_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            full_path = os.path.join(root, file)
            if filter_fn(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    relative_path = os.path.relpath(full_path, root_dir)
                    yield (relative_path, content)

if __name__ == "__main__":
    pass
