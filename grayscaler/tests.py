import time
import unittest

import requests


class Tests(unittest.TestCase):
    def test_flow(self):
        # clear the validating consumer capture buffer
        requests.delete("http://localhost:8000/async/consumers/Result-Validator").raise_for_status()

        # trigger the job
        requests.post("http://localhost:8000/async/producers/Job-Trigger").raise_for_status()

        for _ in range(10):
            time.sleep(1)
            resp = requests.get("http://localhost:8000/async/consumers/Result-Validator")
            resp.raise_for_status()
            har = resp.json()
            if har['log']['entries']:
                print(har['log']['entries'][0]['response']['content']['text'])
                break
        else:
            self.fail("Didn't get the result")
