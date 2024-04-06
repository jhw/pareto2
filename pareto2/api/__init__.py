import os

def file_loader(pkg_root, root_dir=''):
    file_contents = []
    pkg_full_path = os.path.join(root_dir, pkg_root)
    for root, dirs, files in os.walk(pkg_full_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.pyc'):
                continue
            full_path = os.path.join(root, file)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                relative_path = os.path.relpath(full_path, root_dir)
                file_contents.append((relative_path, content))
    return file_contents

if __name__ == "__main__":
    print (file_loader("hello"))
