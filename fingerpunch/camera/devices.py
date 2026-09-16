from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

from fingerpunch.camera.source import CameraUnavailable, FrameSource, OpenCVCamera

logger = logging.getLogger(__name__)

MAX_PROBED_INDEX = 8
DEVICE_SETTING = "camera_device_index"


class SettingsStore(Protocol):
    def get_setting(self, key: str, default: object = None) -> object: ...

    def save_setting(self, key: str, value: object) -> None: ...


def probe_devices(
    max_index: int = MAX_PROBED_INDEX,
    camera_factory: Callable[[int], FrameSource] = OpenCVCamera,
) -> list[int]:
    found: list[int] = []
    for index in range(max_index):
        camera = None
        try:
            camera = camera_factory(index)
            camera.open()
        except CameraUnavailable:
            continue
        except Exception:
            logger.exception("Probing camera %s failed", index)
            continue
        else:
            found.append(index)
        finally:
            if camera is not None:
                camera.close()

    logger.info("Detected camera devices: %s", found)
    return found


def saved_device_index(settings: SettingsStore | None, default: int = 0) -> int:
    if settings is None:
        return default
    value = settings.get_setting(DEVICE_SETTING, default)
    return value if isinstance(value, int) else default


def remember_device_index(settings: SettingsStore | None, index: int) -> None:
    if settings is not None:
        settings.save_setting(DEVICE_SETTING, index)
