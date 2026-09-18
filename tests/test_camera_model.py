import hashlib
import urllib.error

import pytest

from fingerpunch.camera import model
from fingerpunch.camera.model import ModelUnavailable, ensure_model, is_downloaded

PAYLOAD = b"pretend this is a landmark model" * 64
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


class FakeResponse:
    def __init__(self, payload, chunks=3):
        size = max(1, -(-len(payload) // chunks))
        self._parts = [payload[i : i + size] for i in range(0, len(payload), size)]
        self.headers = {"content-length": str(len(payload))}

    def read(self, size):
        return self._parts.pop(0) if self._parts else b""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def served(monkeypatch):
    def serve(payload=PAYLOAD, error=None):
        def opener(url, timeout=None):
            if error is not None:
                raise error
            return FakeResponse(payload)

        monkeypatch.setattr(model.urllib.request, "urlopen", opener)

    monkeypatch.setattr(model, "MODEL_SHA256", DIGEST)
    return serve


class TestDownloading:
    def test_a_missing_model_is_fetched(self, tmp_path, served):
        served()
        target = tmp_path / "hand_landmarker.task"

        result = ensure_model(target)

        assert result == target
        assert target.read_bytes() == PAYLOAD

    def test_an_existing_verified_model_is_not_refetched(self, tmp_path, served, monkeypatch):
        target = tmp_path / "hand_landmarker.task"
        target.write_bytes(PAYLOAD)
        served(error=AssertionError("should not download"))

        assert ensure_model(target) == target

    def test_a_corrupt_existing_model_is_replaced(self, tmp_path, served):
        served()
        target = tmp_path / "hand_landmarker.task"
        target.write_bytes(b"truncated")

        ensure_model(target)

        assert target.read_bytes() == PAYLOAD

    def test_progress_is_reported_while_downloading(self, tmp_path, served):
        served()
        seen = []

        ensure_model(tmp_path / "m.task", on_progress=lambda got, total: seen.append((got, total)))

        assert seen
        assert seen[-1][0] == len(PAYLOAD)
        assert all(total == len(PAYLOAD) for _, total in seen)

    def test_the_parent_directory_is_created(self, tmp_path, served):
        served()
        target = tmp_path / "nested" / "deeper" / "m.task"

        ensure_model(target)

        assert target.is_file()


class TestFailures:
    def test_a_network_error_reports_model_unavailable(self, tmp_path, served):
        served(error=urllib.error.URLError("no route to host"))

        with pytest.raises(ModelUnavailable, match="Could not download"):
            ensure_model(tmp_path / "m.task")

    def test_a_timeout_reports_model_unavailable(self, tmp_path, served):
        served(error=TimeoutError("timed out"))

        with pytest.raises(ModelUnavailable):
            ensure_model(tmp_path / "m.task")

    def test_a_checksum_mismatch_is_rejected(self, tmp_path, served):
        served(payload=b"something else entirely")

        with pytest.raises(ModelUnavailable, match="checksum"):
            ensure_model(tmp_path / "m.task")

    def test_a_rejected_download_is_not_left_behind(self, tmp_path, served):
        served(payload=b"something else entirely")
        target = tmp_path / "m.task"

        with pytest.raises(ModelUnavailable):
            ensure_model(target)

        assert not target.exists()
        assert list(tmp_path.iterdir()) == []

    def test_a_failed_download_leaves_no_partial_file(self, tmp_path, served):
        served(error=urllib.error.URLError("dropped"))

        with pytest.raises(ModelUnavailable):
            ensure_model(tmp_path / "m.task")

        assert [p.name for p in tmp_path.iterdir() if p.suffix != ".part"] == []


class TestVerification:
    def test_a_missing_file_is_not_downloaded(self, tmp_path):
        assert is_downloaded(tmp_path / "absent.task") is False

    def test_a_file_with_the_wrong_contents_is_not_accepted(self, tmp_path, served):
        target = tmp_path / "m.task"
        target.write_bytes(b"wrong")

        assert is_downloaded(target) is False

    def test_a_matching_file_is_accepted(self, tmp_path, served):
        target = tmp_path / "m.task"
        target.write_bytes(PAYLOAD)

        assert is_downloaded(target) is True


@pytest.fixture(autouse=True)
def _no_real_downloads(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a test tried to download over the network")

    monkeypatch.setattr(model.urllib.request, "urlopen", refuse)
