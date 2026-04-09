from __future__ import annotations

import re
import urllib.request
import urllib.error
import json
from typing import Optional


def _parse_version(v: str) -> tuple[int, ...]:
    """Convert '1.2.3' → (1, 2, 3). Strips leading 'v'."""
    v = v.lstrip("v").strip()
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts) if parts else (0,)


def check_for_update(repo: str, current_version: str, timeout: int = 5) -> Optional[dict]:
    """
    Check GitHub releases API for a newer version.

    Returns dict with keys: version, url, download_url (dmg asset if found)
    Returns None if up to date, repo not configured, or check fails.
    """
    if not repo or "/" not in repo:
        return None

    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(
            api_url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "SpendAnalyzer"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None

    latest_tag = data.get("tag_name", "")
    if not latest_tag:
        return None

    if _parse_version(latest_tag) <= _parse_version(current_version):
        return None

    # Find a .dmg asset
    download_url = ""
    for asset in data.get("assets", []):
        if asset.get("name", "").endswith(".dmg"):
            download_url = asset.get("browser_download_url", "")
            break

    return {
        "version": latest_tag.lstrip("v"),
        "release_url": data.get("html_url", f"https://github.com/{repo}/releases"),
        "download_url": download_url,
    }
