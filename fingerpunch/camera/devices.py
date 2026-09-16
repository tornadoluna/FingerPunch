from __future__ import annotations

import logging
from collections.abc import Callable
from typing import NamedTuple, Protocol

from fingerpunch.camera.source import (
    CameraUnavailable,
    FrameSource,
    OpenCVCamera,
    quiet_opencv,
)

logger = logging.getLogger(__name__)

MAX_PROBED_INDEX = 10
MAX_CONSECUTIVE_MISSES = 2
DEVICE_SETTING = "camera_device_index"


class CameraDevice(NamedTuple):
    index: int
    width: int
    height: int

    @property
    def label(self) -> str:
        return f"Camera {self.index} ({self.width}x{self.height})"


class SettingsStore(Protocol):
    def get_setting(self, key: str, default: object = None) -> object: ...

    def save_setting(self, key: str, value: object) -> None: ...


def probe_devices(
    max_index: int = MAX_PROBED_INDEX,
    camera_factory: Callable[[int], FrameSource] = OpenCVCamera,
) -> list[CameraDevice]:
    with quiet_opencv():
        found, failures = _scan(max_index, camera_factory)

    for index, error in failures:
        logger.warning("Probing camera %s failed: %s", index, error)
    logger.info("Detected camera devices: %s", [device.label for device in found])
    return found


def _scan(
    max_index: int,
    camera_factory: Callable[[int], FrameSource],
) -> tuple[list[CameraDevice], list[tuple[int, Exception]]]:
    found: list[CameraDevice] = []
    failures: list[tuple[int, Exception]] = []
    misses = 0

    for index in range(max_index):
        device, error = _probe_one(index, camera_factory)
        if error is not None:
            failures.append((index, error))

        if device is not None:
            found.append(device)
            misses = 0
            continue

        misses += 1
        if misses >= MAX_CONSECUTIVE_MISSES and found:
            break

    return found, failures


def _probe_one(
    index: int,
    camera_factory: Callable[[int], FrameSource],
) -> tuple[CameraDevice | None, Exception | None]:
    camera = None
    try:
        camera = camera_factory(index)
        camera.open()
        frame = camera.read()
        if frame is None:
            return None, None
        return CameraDevice(index, frame.width, frame.height), None
    except CameraUnavailable:
        return None, None
    except Exception as error:  # noqa: BLE001
        return None, error
    finally:
        if camera is not None:
            camera.close()


def delivers_frames(
    index: int,
    camera_factory: Callable[[int], FrameSource] = OpenCVCamera,
) -> bool:
    with quiet_opencv():
        device, _ = _probe_one(index, camera_factory)
    return device is not None


def saved_device_index(settings: SettingsStore | None, default: int = 0) -> int:
    if settings is None:
        return default
    value = settings.get_setting(DEVICE_SETTING, default)
    return value if isinstance(value, int) else default


def remember_device_index(settings: SettingsStore | None, index: int) -> None:
    if settings is not None:
        settings.save_setting(DEVICE_SETTING, index)
