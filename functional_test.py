import api
import datetime

import requests
import hashlib
import json


def get_valid_auth():
    return hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode()).hexdigest()


def test_empty_page():
    address = 'http://127.0.0.1:8080/method/'
    valid_json = {"account": "horns&hoofs", "login": "admin", "method": "clients_interests",
                  "token": get_valid_auth(),
                  "arguments": {"client_ids": [1, 2, 3, 4], "date": "20.07.2017"}}
    req = requests.post(address, data=json.dumps(valid_json))
    assert req.status_code == 200
