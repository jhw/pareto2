class MyBaseClass:

    def __init__(self):
        pass

class MyMixin:

    def hello(self):
        print ("hello")
    
class MyClass(MyBaseClass, MyMixin):

    def __init__(self):
        MyBaseClass.__init__(self)
                
if __name__=="__main__":
    obj=MyClass()
    obj.hello()
