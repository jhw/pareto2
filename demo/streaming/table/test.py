from pareto2.test import Pareto2TestBase

import unittest.mock as mock

import os, unittest

class DemoStreamingTableTest(Pareto2TestBase):

    def setUp(self):
        self.env={}

    def test_handler(self):
        with mock.patch.dict(os.environ, self.env):
            from demo.streaming.table.index import handler
            handler({})

    def tearDown(self):
        pass
    
if __name__=="__main__":
    unittest.main()
