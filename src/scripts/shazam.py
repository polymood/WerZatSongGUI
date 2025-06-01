# src/scripts/shazam.py

import asyncio
from typing import Any, Dict, Optional

from shazamio import Shazam


async def recognize_shazam(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Use shazamio to identify the given audio file.
    Returns a dict {"service": "Shazam", "title": ..., "artist": ..., "share_url": ...}
    or None if no match.
    """
    try:
        out = await Shazam().recognize_song(file_path)
        if out.get("track"):
            track = out["track"]
            return {
                "service": "Shazam",
                "title": track.get("title", ""),
                "artist": track.get("subtitle", ""),
                "share_url": track.get("share", {}).get("href", ""),
            }
        return None
    except Exception:
        return None


def recognize_shazam_sync(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Synchronous wrapper around the async recognize_shazam function.
    """
    return asyncio.run(recognize_shazam(file_path))
