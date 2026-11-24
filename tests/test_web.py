import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
from cycle_project.web import Handler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def read(self, path):
        with urlopen(self.base+path, timeout=5) as r:
            return json.load(r)

    def test_comparison(self):
        data = self.read("/api/compare?mu=3&lam=4")
        for r in data.values():
            self.assertEqual((r["status"], r["mu"], r["lam"]), ("cycle", 3, 4))

    def test_bad_input(self):
        for path in ("/api/compare?length=-1", "/api/compare?mu=abc", "/api/compare?lam=0"):
            with self.assertRaises(HTTPError) as error:
                self.read(path)
            self.assertEqual(error.exception.code, 400)

    def test_agent_retry(self):
        data = self.read("/api/agent?scenario=retry")
        self.assertEqual((data["status"], data["actions"]), ("terminated", 8))
