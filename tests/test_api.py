import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from swarscribe.api import MAX_BODY, create_app
from swarscribe.app import persist_result
from swarscribe.config import Config
from swarscribe.transcribe import BackendUnavailable, Transcript

from test_reliability import wav


class ApiTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        env = patch.dict("os.environ", SWARSCRIBE_HOME=temp.name)
        env.start()
        self.addCleanup(env.stop)
        self.client = TestClient(create_app(), base_url="http://127.0.0.1",
                                 client=("127.0.0.1", 1234))
        self.addCleanup(self.client.close)
        self.local = {"X-SwarScribe-Local": "1", "Origin": "http://127.0.0.1"}

    def test_same_origin_dashboard_and_persistent_dictionary(self):
        self.assertIn("Your dictation dashboard", self.client.get("/").text)
        self.assertEqual(self.client.get("/dashboard.js").status_code, 200)
        response = self.client.put("/dictionary", headers=self.local,
                                   json={"entries": {"Super Base": "Supabase"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Config.load().dictionary, {"super base": "Supabase"})
        self.assertEqual(self.client.post("/clean", json={"text": "super base"}).json()["text"], "Supabase.")

    def test_rejects_remote_and_cross_origin_mutation(self):
        self.assertEqual(self.client.get("/stats", headers={"Host": "elsewhere.test"}).status_code, 403)
        self.assertEqual(self.client.get("/stats", headers={"Origin": "https://elsewhere.test"}).status_code, 403)
        self.assertEqual(self.client.put("/snippets", json={"entries": {}}).status_code, 403)
        self.assertEqual(self.client.post("/clean", content="{}").status_code, 415)

    def test_invalid_bodies_and_model_failure(self):
        invalid = self.client.post("/transcribe", json={"wav_base64": "!secret?"})
        self.assertEqual(invalid.status_code, 422)
        self.assertNotIn("secret", invalid.text)
        self.assertEqual(self.client.post("/transcribe",
                                          json={"wav_base64": wav(frames=8000 * 121, rate=8000)}).status_code, 413)
        oversize = self.client.post("/transcribe", headers={"Content-Type": "application/json"},
                                    content=(b"x" * (1024 * 1024) for _ in range(MAX_BODY // (1024 * 1024) + 1)))
        self.assertEqual(oversize.status_code, 413)
        with patch.object(Config, "backend", side_effect=BackendUnavailable("Install the Whisper model.")):
            response = self.client.post("/transcribe", json={"wav_base64": wav()})
            self.assertEqual(response.status_code, 503)
            self.assertIn("Whisper", response.json()["detail"])

    def test_history_search_export_delete_and_accurate_stats(self):
        persist_result("my notes", "My notes.", 6, Config())
        data = self.client.get("/history?q=NOTES").json()["entries"]
        self.assertEqual(len(data), 1)
        self.assertIn("My notes.", self.client.get("/history/export").text)
        self.assertEqual(self.client.get("/stats").json()["sessions"], 1)
        self.assertEqual(self.client.delete("/history/" + data[0]["id"], headers=self.local).status_code, 200)
        self.assertEqual(self.client.get("/history").json(), {"entries": []})

    def test_paired_api_requires_token_https_and_only_exposes_speech(self):
        token = "test_" + "A" * 39
        paired = create_app(lan_token=token, lan_hostname="desktop.test")
        secure = TestClient(paired, base_url="https://desktop.test")
        cleartext = TestClient(paired, base_url="http://desktop.test")
        self.addCleanup(secure.close)
        self.addCleanup(cleartext.close)
        authorized = {"Authorization": f"Bearer {token}"}
        self.assertEqual(secure.get("/health").status_code, 401)
        self.assertEqual(cleartext.get("/health", headers=authorized).status_code, 403)
        self.assertEqual(secure.get("/health", headers=authorized).json()["paired"], True)
        self.assertEqual(secure.get("/history", headers=authorized).status_code, 404)
        with patch.object(Config, "backend"), patch("swarscribe.api.transcribe_wav_bytes",
                                                    return_value=Transcript("hello", "test", "en")):
            response = secure.post("/transcribe", json={"wav_base64": wav()}, headers=authorized)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Hello.")
        self.assertEqual(self.client.get("/history").json(), {"entries": []})
