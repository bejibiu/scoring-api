import api
import datetime
import unittest
import requests
import hashlib
import json


class FuncTest(unittest.TestCase):

    def get_valid_auth(self):
        return hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode()).hexdigest()

    def setUp(self):
        self.address = 'http://127.0.0.1:8080/method/'
        self.context = {}
        self.headers = {}
        self.settings = {}
        self.valid_json = {"account": "horns&hoofs", "login": "admin", "method": "clients_interests",
                           "token": self.get_valid_auth(),
                           "arguments": {"client_ids": [1, 2, 3, 4], "date": "20.07.2017"}}

    def test_empty_page(self):
        req = requests.post(self.address, data=json.dumps(self.valid_json))
        assert req.status_code == 200
