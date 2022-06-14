from pareto2.test import Pareto2TestBase

import unittest.mock as mock

import json, os, unittest

class DemoHelloPostTest(Pareto2TestBase):

    def setUp(self):
        self.env={}

    def test_handler(self):
        with mock.patch.dict(os.environ, self.env):
            from demo.hello.get.index import handler
            event={"queryStringParameters": {"message": "Hello world!"}}
            resp=handler(event)
            self.assertTrue("statusCode" in resp)
            self.assertEqual(resp["statusCode"], 200)
            self.assertTrue("body" in resp)
            respbody=json.loads(resp["body"])
            self.assertTrue("message" in respbody)
            message=respbody["message"]
            self.assertTrue("Hello world!" in message)

    def tearDown(self):
        pass
    
if __name__=="__main__":
    unittest.main()
