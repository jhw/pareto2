import os, re, yaml

def refactor_src(pat, rep, root):
    def refactor(tokens):
        path="/".join(tokens)
        for entry in os.listdir(path):
            newtokens=tokens+[entry]
            filename="/".join(newtokens)
            if os.path.isdir(filename):
                if not filename=="__pycache__":
                    refactor(newtokens)
            elif filename.endswith("pyc"):
                pass
            else:
                text=open(filename).read()
                newtext=re.sub(pat, rep, text)
                newfilename=re.sub(pat, rep, filename)
                if (text!=newtext or
                    filename!=newfilename):
                    print (newfilename)
                    dest=open(newfilename, 'w')
                    dest.write(newtext)
                    dest.close()
    refactor(root.split("/"))
                        
if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 4:
            raise RuntimeError("please enter pat, rep, root")
        pat, rep, root = sys.argv[1:5]
        refactor_src(pat, rep, root)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
