"""Configuration for the game launcher and updater.

Update the values in this file for your real project:
- GITHUB_OWNER
- GITHUB_REPO
- GAME_EXE_NAME
- RELEASE_ASSET_NAME
"""
from pathlib import Path

# -----------------------------
# Project / app identification
# -----------------------------
APP_NAME = "Help-tam Game"
GAME_EXE_NAME = "game.exe"  # <-- change to your main game exe name
UPDATER_EXE_NAME = "updater.exe"  # if you package updater to exe

# -----------------------------
# Local version storage
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
LOCAL_VERSION_FILE = BASE_DIR / "version.json"

# -----------------------------
# GitHub source configuration
# -----------------------------
GITHUB_OWNER = "your-owner"  # <-- change: GitHub owner
GITHUB_REPO = "your-repo"  # <-- change: GitHub repo name

# Preferred source: GitHub Releases
USE_GITHUB_RELEASES = True

# Optional fallback source (raw version file)
USE_RAW_VERSION_FALLBACK = True
RAW_VERSION_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/version.json"
)

# Release asset expected in latest release
RELEASE_ASSET_NAME = "game-build-windows.zip"  # <-- change: release zip name

# URLs built from owner/repo
GITHUB_API_LATEST_RELEASE = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
GITHUB_REPO_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"

# -----------------------------
# Update behavior
# -----------------------------
REQUEST_TIMEOUT_SECONDS = 20
DOWNLOAD_CHUNK_SIZE = 1024 * 128

# Folders to preserve while replacing files
PRESERVE_DIRS = {"saves", "config", "userdata"}

# Log files
LAUNCHER_LOG = BASE_DIR / "launcher.log"
UPDATER_LOG = BASE_DIR / "updater.log"
