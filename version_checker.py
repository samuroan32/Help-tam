"""Version checking helpers for launcher/updater.

Provides:
- semantic version parsing + comparison
- local version loading
- latest version + download URL from GitHub
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

import config

SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


class VersionError(Exception):
    """Raised when version information cannot be parsed or fetched."""


@dataclass
class ReleaseInfo:
    version: str
    download_url: Optional[str]
    release_page: str
    source: str  # e.g. "github_release" or "raw_version"


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse semantic version like 1.2.3 or v1.2.3."""
    value = version.strip()
    match = SEMVER_RE.match(value)
    if not match:
        raise VersionError(f"Некорректный формат версии: '{version}'")
    return tuple(int(part) for part in match.groups())


def is_version_less(local_version: str, remote_version: str) -> bool:
    """Return True if local version is lower than remote version."""
    return parse_semver(local_version) < parse_semver(remote_version)


def read_local_version(path: Path = config.LOCAL_VERSION_FILE) -> str:
    """Read local version from version.json."""
    if not path.exists():
        raise VersionError(f"Локальный файл версии не найден: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        version = str(data.get("version", "")).strip()
        if not version:
            raise VersionError("В version.json отсутствует поле 'version'")
        parse_semver(version)
        return version
    except json.JSONDecodeError as exc:
        raise VersionError(f"Ошибка чтения version.json: {exc}") from exc


def _extract_asset_url_from_release(release_json: dict) -> Optional[str]:
    assets = release_json.get("assets", [])
    # try exact name
    for asset in assets:
        if asset.get("name") == config.RELEASE_ASSET_NAME:
            return asset.get("browser_download_url")
    # fallback: first zip asset
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        if name.endswith(".zip"):
            return asset.get("browser_download_url")
    return None


def fetch_latest_release_info() -> ReleaseInfo:
    """Fetch latest version from GitHub Releases (preferred) or raw version fallback."""
    errors: list[str] = []

    if config.USE_GITHUB_RELEASES:
        try:
            response = requests.get(
                config.GITHUB_API_LATEST_RELEASE,
                timeout=config.REQUEST_TIMEOUT_SECONDS,
                headers={"Accept": "application/vnd.github+json"},
            )
            if response.status_code != 200:
                raise VersionError(
                    f"GitHub API вернул {response.status_code}: {response.text[:200]}"
                )

            release = response.json()
            tag_name = str(release.get("tag_name", "")).strip()
            if not tag_name:
                raise VersionError("В GitHub release отсутствует tag_name")
            parse_semver(tag_name)

            return ReleaseInfo(
                version=tag_name.lstrip("v"),
                download_url=_extract_asset_url_from_release(release),
                release_page=str(release.get("html_url") or config.GITHUB_REPO_URL),
                source="github_release",
            )
        except (requests.RequestException, ValueError, VersionError) as exc:
            errors.append(f"GitHub Releases: {exc}")

    if config.USE_RAW_VERSION_FALLBACK:
        try:
            response = requests.get(
                config.RAW_VERSION_URL,
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                raise VersionError(
                    f"Raw version URL вернул {response.status_code}: {response.text[:200]}"
                )

            raw = response.text.strip()
            version_value: Optional[str] = None
            # raw can be plain text (1.2.3) or json ({"version":"1.2.3"})
            if raw.startswith("{"):
                payload = json.loads(raw)
                version_value = str(payload.get("version", "")).strip()
            else:
                version_value = raw

            if not version_value:
                raise VersionError("Не удалось извлечь версию из raw-источника")
            parse_semver(version_value)

            return ReleaseInfo(
                version=version_value.lstrip("v"),
                download_url=None,
                release_page=config.GITHUB_REPO_URL,
                source="raw_version",
            )
        except (requests.RequestException, ValueError, VersionError) as exc:
            errors.append(f"Raw version fallback: {exc}")

    raise VersionError(
        "Не удалось получить актуальную версию. Причины: " + " | ".join(errors)
    )
