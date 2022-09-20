import re

Text="""
def handler(tablename=os.environ["TABLE_NAME"]):
  print ("HELLO_WORLD")
"""

if __name__=="__main__":
    variables=[tok[1:-1].lower().replace("_", "-")
               for tok in re.findall(r"os\.environ\[(.*?)\]",
                                     re.sub("\\s", "", Text))
               if (tok.upper()==tok and
                   len(tok) > 3)]
    print (variables)
