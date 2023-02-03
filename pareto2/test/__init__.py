import unittest, warnings

FunctionName="test-function"

class Context:

    def __init__(self, functionname=FunctionName):
        self.function_name=functionname

class Pareto2TestBase(unittest.TestCase):

    """
    - https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file
    - https://stackoverflow.com/a/63902279/124179
    - https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
    """
    
    @classmethod
    def setUpClass(cls):
        def init_stdout_logger():
            import logging, sys
            logger=logging.getLogger()
            if not logger.handlers:
                logger.setLevel(logging.INFO)    
                sh=logging.StreamHandler(sys.stdout)
                formatter=logging.Formatter('[%(levelname)s] %(message)s')
                sh.setFormatter(formatter)
                logger.addHandler(sh)
        init_stdout_logger()
        warnings.simplefilter("ignore")

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.env={}

if __name__=="___main__":
    pass
