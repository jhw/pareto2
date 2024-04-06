import os

def file_loader(root_dir):
    file_contents = []    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']        
        for file in files:
            if file.endswith('.pyc'):
                continue            
            full_path = os.path.join(root, file)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents.append((full_path, content))
    return file_contents

if __name__ == "__main__":
    print (file_loader("hello"))
