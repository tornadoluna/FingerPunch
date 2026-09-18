from __future__ import annotations

import hashlib
import logging
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from fingerpunch.paths import app_data_dir

logger = logging.getLogger(__name__)

MODEL_FILENAME = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker"
    "/hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
MODEL_BYTES = 7819105
DOWNLOAD_TIMEOUT = 60
CHUNK_BYTES = 64 * 1024


class ModelUnavailable(RuntimeError):
    pass


def model_path() -> Path:
    return app_data_dir() / "models" / MODEL_FILENAME


def is_downloaded(path: Path | None = None) -> bool:
    path = model_path() if path is None else path
    return path.is_file() and _digest(path) == MODEL_SHA256


def ensure_model(
    path: Path | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> Path:
    path = model_path() if path is None else path
    if is_downloaded(path):
        return path

    logger.info("Downloading the hand landmark model to %s", path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        downloaded = _download(path.parent, on_progress)
    except (OSError, urllib.error.URLError, TimeoutError) as error:
        raise ModelUnavailable(f"Could not download the hand landmark model: {error}") from error

    digest = _digest(downloaded)
    if digest != MODEL_SHA256:
        downloaded.unlink(missing_ok=True)
        raise ModelUnavailable(
            f"The downloaded hand landmark model did not match its checksum ({digest})"
        )

    downloaded.replace(path)
    logger.info("Hand landmark model ready at %s", path)
    return path


def _download(directory: Path, on_progress: Callable[[int, int], None] | None) -> Path:
    handle, temporary = tempfile.mkstemp(dir=directory, suffix=".part")
    target = Path(temporary)
    received = 0

    with open(handle, "wb") as sink, urllib.request.urlopen(
        MODEL_URL, timeout=DOWNLOAD_TIMEOUT
    ) as response:
        total = int(response.headers.get("content-length") or MODEL_BYTES)
        while True:
            chunk = response.read(CHUNK_BYTES)
            if not chunk:
                break
            sink.write(chunk)
            received += len(chunk)
            if on_progress is not None:
                on_progress(received, total)

    return target


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()
