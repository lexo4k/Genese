import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from genese_dashboard import Handler, PAGE


class GeneseMobilePwaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_dashboard_declares_installable_app(self):
        self.assertIn('rel="manifest"', PAGE)
        self.assertIn("serviceWorker.register", PAGE)

    def test_manifest_is_valid_and_mobile_installable(self):
        with urlopen(self.base + "/manifest.webmanifest", timeout=2) as response:
            manifest = json.loads(response.read().decode())
        self.assertEqual(manifest["name"], "GÊNESE PAY")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "/")

    def test_service_worker_is_served_and_does_not_cache_api(self):
        with urlopen(self.base + "/service-worker.js", timeout=2) as response:
            body = response.read().decode()
        self.assertIn('url.pathname.startsWith("/api/")', body)
        self.assertIn("caches.match", body)

    def test_cross_origin_miner_control_is_rejected(self):
        req = Request(self.base + "/api/miner/start", method="POST",
                      headers={"Origin": "https://attacker.invalid"})
        with self.assertRaises(HTTPError) as error:
            urlopen(req, timeout=2)
        self.assertEqual(error.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
