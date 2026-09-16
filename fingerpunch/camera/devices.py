from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple, Protocol

from fingerpunch.camera.source import (
    DEFAULT_RESOLUTION,
    CameraUnavailable,
    FrameSource,
    OpenCVCamera,
    quiet_opencv,
)

logger = logging.getLogger(__name__)

V4L_SYSFS = Path("/sys/class/video4linux")
MAX_PROBED_INDEX = 10
MAX_CONSECUTIVE_MISSES = 2
DEVICE_SETTING = "camera_device_index"
RESOLUTION_SETTING = "camera_resolution"
RESOLUTION_CHOICES: tuple[tuple[int, int], ...] = ((640, 480), (1280, 720), (1920, 1080))


class CameraDevice(NamedTuple):
    index: int
    width: int
    height: int
    name: str | None = None

    @property
    def label(self) -> str:
        who = self.name or f"Camera {self.index}"
        return f"{who} ({self.width}x{self.height})"


def device_name(index: int, sysfs: Path | None = None) -> str | None:
    sysfs = V4L_SYSFS if sysfs is None else sysfs
    try:
        name = (sysfs / f"video{index}" / "name").read_text().strip()
    except OSError:
        return None
    return _tidy_name(name) or None


def _tidy_name(name: str) -> str:
    head, separator, tail = name.partition(": ")
    if separator and tail and head.lower().startswith(tail.lower()):
        return head.strip()
    return name.strip()


def is_capture_node(index: int, sysfs: Path | None = None) -> bool:
    sysfs = V4L_SYSFS if sysfs is None else sysfs
    try:
        return int((sysfs / f"video{index}" / "index").read_text().strip()) == 0
    except (OSError, ValueError):
        return True


class SettingsStore(Protocol):
    def get_setting(self, key: str, default: object = None) -> object: ...

    def save_setting(self, key: str, value: object) -> None: ...


def probe_devices(
    max_index: int = MAX_PROBED_INDEX,
    camera_factory: Callable[[int], FrameSource] = OpenCVCamera,
    sysfs: Path | None = None,
) -> list[CameraDevice]:
    with quiet_opencv():
        found, failures = _scan(max_index, camera_factory, sysfs)

    for index, error in failures:
        logger.warning("Probing camera %s failed: %s", index, error)
    logger.info("Detected camera devices: %s", [device.label for device in found])
    return found


def _scan(
    max_index: int,
    camera_factory: Callable[[int], FrameSource],
    sysfs: Path | None = None,
) -> tuple[list[CameraDevice], list[tuple[int, Exception]]]:
    found: list[CameraDevice] = []
    failures: list[tuple[int, Exception]] = []
    misses = 0

    for index in range(max_index):
        if not is_capture_node(index, sysfs):
            continue

        device, error = _probe_one(index, camera_factory, sysfs)
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
    sysfs: Path | None = None,
) -> tuple[CameraDevice | None, Exception | None]:
    camera = None
    try:
        camera = camera_factory(index)
        camera.open()
        frame = camera.read()
        if frame is None:
            return None, None
        return CameraDevice(index, frame.width, frame.height, device_name(index, sysfs)), None
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


def saved_resolution(
    settings: SettingsStore | None,
    default: tuple[int, int] = DEFAULT_RESOLUTION,
) -> tuple[int, int]:
    if settings is None:
        return default

    value = settings.get_setting(RESOLUTION_SETTING, None)
    if (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(part, int) and part > 0 for part in value)
    ):
        return (value[0], value[1])
    return default


def remember_resolution(settings: SettingsStore | None, resolution: tuple[int, int]) -> None:
    if settings is not None:
        settings.save_setting(RESOLUTION_SETTING, list(resolution))
