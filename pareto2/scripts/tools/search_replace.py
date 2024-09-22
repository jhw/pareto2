import os
import re
import sys

def refactor_src(pat, rep, root):
    def refactor(tokens):
        path = "/".join(tokens)
        for entry in os.listdir(path):
            new_tokens = tokens+[entry]
            file_name = "/".join(new_tokens)
            if os.path.isdir(file_name):
                if not file_name == "__pycache__":
                    refactor(new_tokens)
            elif file_name.endswith("pyc"):
                pass
            else:
                text = open(file_name).read()
                new_text = re.sub(pat, rep, text)
                new_file_name = re.sub(pat, rep, file_name)
                if (text != new_text or
                    file_name != new_file_name):
                    print (new_file_name)
                    dest = open(new_file_name, 'w')
                    dest.write(new_text)
                    dest.close()
    refactor(root.split("/"))
                        
if __name__ == "__main__":
    try:
        if len(sys.argv) < 4:
            raise RuntimeError("please enter pat, rep, root")
        pat, rep, root = sys.argv[1:5]
        refactor_src(pat, rep, root)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
