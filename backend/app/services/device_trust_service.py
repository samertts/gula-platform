from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.security.device")


class TrustLevel(Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    TRUSTED = "trusted"


class DevicePlatform(Enum):
    ANDROID = "android"
    IOS = "ios"
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    WEB = "web"


@dataclass
class DeviceFingerprint:
    device_id: str = ""
    platform: DevicePlatform = DevicePlatform.WEB
    os_version: str = ""
    browser: str = ""
    browser_version: str = ""
    screen_resolution: str = ""
    language: str = ""
    timezone: str = ""
    user_agent: str = ""
    hardware_concurrency: int = 0
    device_memory: float = 0.0
    installed_fonts: list[str] = field(default_factory=list)
    canvas_fingerprint: str = ""
    webgl_fingerprint: str = ""
    audio_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "platform": self.platform.value,
            "os_version": self.os_version,
            "browser": self.browser,
            "browser_version": self.browser_version,
            "screen_resolution": self.screen_resolution,
            "language": self.language,
            "timezone": self.timezone,
            "user_agent": self.user_agent,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
        }

    def compute_hash(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class TrustedDevice:
    device_id: str = ""
    user_id: str = ""
    fingerprint_hash: str = ""
    trust_level: TrustLevel = TrustLevel.UNKNOWN
    first_seen: float = 0.0
    last_seen: float = 0.0
    successful_logins: int = 0
    failed_attempts: int = 0
    is_active: bool = True
    is_current: bool = False
    device_name: str = ""
    platform: str = ""
    os_version: str = ""
    browser: str = ""
    browser_version: str = ""
    geolocation: str = ""
    ip_address: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "user_id": self.user_id,
            "trust_level": self.trust_level.value,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "successful_logins": self.successful_logins,
            "failed_attempts": self.failed_attempts,
            "is_active": self.is_active,
            "is_current": self.is_current,
            "device_name": self.device_name,
            "platform": self.platform,
            "browser": self.browser,
        }


class DeviceTrustService:
    def __init__(self):
        self._devices: dict[str, TrustedDevice] = {}
        self._user_devices: dict[str, list[str]] = {}
        self._fingerprint_cache: dict[str, str] = {}

    def register_device(
        self,
        user_id: str,
        fingerprint: DeviceFingerprint,
        device_name: str = "",
        ip_address: str = "",
        geolocation: str = "",
    ) -> TrustedDevice:
        fp_hash = fingerprint.compute_hash()

        existing = self._find_by_fingerprint(user_id, fp_hash)
        if existing:
            existing.last_seen = time.time()
            existing.ip_address = ip_address
            existing.geolocation = geolocation
            if existing.trust_level == TrustLevel.UNKNOWN:
                existing.trust_level = TrustLevel.LOW
            return existing

        device_id = hashlib.sha256(f"{user_id}:{fp_hash}:{time.time()}".encode()).hexdigest()[:16]
        now = time.time()

        device = TrustedDevice(
            device_id=device_id,
            user_id=user_id,
            fingerprint_hash=fp_hash,
            trust_level=TrustLevel.UNKNOWN,
            first_seen=now,
            last_seen=now,
            is_active=True,
            device_name=device_name or f"{fingerprint.platform.value} {fingerprint.browser}",
            platform=fingerprint.platform.value,
            os_version=fingerprint.os_version,
            browser=fingerprint.browser,
            browser_version=fingerprint.browser_version,
            ip_address=ip_address,
            geolocation=geolocation,
        )

        self._devices[device_id] = device
        self._user_devices.setdefault(user_id, []).append(device_id)
        self._fingerprint_cache[fp_hash] = device_id

        self._evaluate_trust_level(device)
        return device

    def record_successful_login(self, device_id: str) -> None:
        device = self._devices.get(device_id)
        if not device:
            return
        device.successful_logins += 1
        device.last_seen = time.time()
        device.is_current = True
        self._evaluate_trust_level(device)

    def record_failed_attempt(self, device_id: str) -> None:
        device = self._devices.get(device_id)
        if not device:
            return
        device.failed_attempts += 1
        if device.failed_attempts >= 5:
            device.trust_level = TrustLevel.LOW
            device.is_active = False
            logger.warning("Device %s deactivated after %d failed attempts", device_id, device.failed_attempts)

    def get_device(self, device_id: str) -> TrustedDevice | None:
        return self._devices.get(device_id)

    def get_user_devices(self, user_id: str) -> list[TrustedDevice]:
        device_ids = self._user_devices.get(user_id, [])
        return [self._devices[did] for did in device_ids if did in self._devices]

    def get_trust_level(self, device_id: str) -> TrustLevel:
        device = self._devices.get(device_id)
        if not device:
            return TrustLevel.UNKNOWN
        return device.trust_level

    def verify_device(self, device_id: str, fingerprint: DeviceFingerprint) -> bool:
        device = self._devices.get(device_id)
        if not device or not device.is_active:
            return False
        fp_hash = fingerprint.compute_hash()
        return device.fingerprint_hash == fp_hash

    def deactivate_device(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False
        device.is_active = False
        device.trust_level = TrustLevel.LOW
        return True

    def set_current_device(self, user_id: str, device_id: str) -> None:
        for did in self._user_devices.get(user_id, []):
            d = self._devices.get(did)
            if d:
                d.is_current = did == device_id

    def _find_by_fingerprint(self, user_id: str, fp_hash: str) -> TrustedDevice | None:
        device_id = self._fingerprint_cache.get(fp_hash)
        if device_id:
            device = self._devices.get(device_id)
            if device and device.user_id == user_id:
                return device
        for did in self._user_devices.get(user_id, []):
            device = self._devices.get(did)
            if device and device.fingerprint_hash == fp_hash:
                return device
        return None

    def _evaluate_trust_level(self, device: TrustedDevice) -> None:
        if device.trust_level == TrustLevel.TRUSTED:
            return

        if device.successful_logins >= 10 and device.failed_attempts == 0:
            device.trust_level = TrustLevel.TRUSTED
        elif device.successful_logins >= 5:
            device.trust_level = TrustLevel.HIGH
        elif device.successful_logins >= 2:
            device.trust_level = TrustLevel.MEDIUM
        elif device.successful_logins >= 1:
            device.trust_level = TrustLevel.LOW


def compute_device_fingerprint(
    user_agent: str = "",
    platform: str = "web",
    screen_resolution: str = "",
    language: str = "",
    timezone: str = "",
    hardware_concurrency: int = 0,
    device_memory: float = 0.0,
) -> DeviceFingerprint:
    raw = f"{user_agent}|{platform}|{screen_resolution}|{language}|{timezone}|{hardware_concurrency}|{device_memory}"
    device_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
    try:
        plat = DevicePlatform(platform.lower())
    except ValueError:
        plat = DevicePlatform.WEB

    return DeviceFingerprint(
        device_id=device_id,
        platform=plat,
        os_version="",
        browser=_extract_browser(user_agent),
        browser_version=_extract_browser_version(user_agent),
        screen_resolution=screen_resolution,
        language=language,
        timezone=timezone,
        user_agent=user_agent,
        hardware_concurrency=hardware_concurrency,
        device_memory=device_memory,
    )


def _extract_browser(ua: str) -> str:
    for name in ["Chrome", "Firefox", "Safari", "Edge", "Opera", "Brave"]:
        if name.lower() in ua.lower():
            return name
    return "Unknown"


def _extract_browser_version(ua: str) -> str:
    import re
    m = re.search(r"(Chrome|Firefox|Safari|Edge|Opera)/(\d+\.\d+)", ua)
    if m:
        return m.group(2)
    return ""
