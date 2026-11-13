"""Opt-in real Whisper → API → cleanup → history smoke for the JFK fixture."""

import base64
import os
import sys
import tempfile
import time
import wave
from pathlib import Path

from fastapi.testclient import TestClient

from swarscribe.api import create_app
from swarscribe.config import Config


def main(audio_file: Path) -> None:
    previous = os.getenv("SWARSCRIBE_HOME")
    source_models = (Path(previous) if previous else Path.home() / ".swarscribe") / "models"
    with tempfile.TemporaryDirectory() as state:
        # Model files stay in the configured cache; put verification data elsewhere.
        os.environ["SWARSCRIBE_HOME"] = state
        (Path(state) / "models").symlink_to(source_models, target_is_directory=True)
        Config(engine="whisper", model="tiny", language="en", local_only=True,
               dictionary={"fellow americans": "fellow Americans"}).save()
        with wave.open(str(audio_file), "rb") as wav:
            duration = wav.getnframes() / wav.getframerate()
        payload = {"wav_base64": base64.b64encode(audio_file.read_bytes()).decode("ascii")}
        with TestClient(create_app(), base_url="http://127.0.0.1", client=("127.0.0.1", 1)) as client:
            timings = []
            for _ in range(2):
                start = time.perf_counter()
                response = client.post("/transcribe", json=payload)
                timings.append(time.perf_counter() - start)
                assert response.status_code == 200, response.text
                result = response.json()
                assert "ask not" in result["raw"].lower(), result["raw"]
                assert "fellow Americans" in result["text"], result["text"]
                assert result["segments"] and result["segments"][0]["end"] > 0
            assert client.get("/stats").json()["sessions"] == 2
        with TestClient(create_app(), base_url="http://127.0.0.1", client=("127.0.0.1", 1)) as restarted:
            assert len(restarted.get("/history?q=ask").json()["entries"]) == 2
        print(f"{duration:.2f}s audio; first request {timings[0]:.2f}s; cached {timings[1]:.2f}s")
        print(result["text"])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
