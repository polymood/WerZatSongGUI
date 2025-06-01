# src/scripts/musicbrainz.py

import asyncio
import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from scripts.consts import (
    ACOUSTID_TRACK_ENDPOINT,
    ACOUSTID_LOOKUP_ENDPOINT,
    MAX_CORES_ALLOWED,
    MUSICBRAINZ_LIMIT,
    TEMP_FOLDER,
)
from scripts.helpers import trim_extension

# Regex for blacklisted AcoustID results
BLACKLISTED_RESULTS_REGEX = re.compile(r"^94765\d{3}$")
INTERVAL_DELAY = 0.6  # seconds between API calls


async def is_blacklisted(track_id: str) -> bool:
    """
    Check if a given AcoustID track_id is blacklisted by querying MusicBrainz.
    Returns True if blacklisted, False otherwise.
    """
    try:
        url = f"{ACOUSTID_TRACK_ENDPOINT}/{track_id}"
        resp = requests.get(url, timeout=10)
        html = resp.text
        matches = re.findall(r'<a\shref="/fingerprint/\d+">(\d+)</a>', html)
        if len(matches) > 1:
            return False
        fingerprint_id = matches[0]
        return bool(BLACKLISTED_RESULTS_REGEX.match(fingerprint_id))
    except Exception:
        return False


async def search_acoustid(
    api_key: str, duration: int, fingerprint: str
) -> Dict[str, Any]:
    """
    Perform a single AcoustID lookup. Returns {"error": bool, "results": list} or {}.
    """
    response: Dict[str, Any] = {"error": False, "results": None}
    try:
        params = {
            "format": "json",
            "client": api_key,
            "duration": str(duration),
            "fingerprint": fingerprint,
        }
        resp = requests.get(ACOUSTID_LOOKUP_ENDPOINT, params=params, timeout=20)
        json_data = resp.json()
        if json_data.get("status") != "ok":
            if json_data.get("error", {}).get("message") == "invalid API key":
                response["error"] = True
            return response

        all_results = []
        for result in json_data.get("results", []):
            track_id = result.get("id")
            if not track_id:
                continue
            black = await is_blacklisted(track_id)
            if not black:
                all_results.append(result)

        response["results"] = all_results
        return response

    except Exception:
        return response


def chunkify(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split list `lst` into `n` chunks (round-robin distribution).
    """
    chunks = [[] for _ in range(n)]
    for idx, val in enumerate(lst):
        chunks[idx % n].append(val)
    return chunks


async def _search_worker(
    api_key: str,
    fingerprint_items: List[Tuple[int, str]],
    min_duration: int,
    max_duration: int,
    result_queue: asyncio.Queue,
):
    """
    Each worker loops over (offset, fingerprint) pairs. For each pair, it increments
    duration from min_duration to max_duration in steps of 5, calling search_acoustid().
    On finding a match, it puts ("match", results, duration, offset) into the queue and returns.
    If an API key is invalid, it puts ("quit", None, None, None). Otherwise, once done, it returns.
    """
    for offset, fp_string in fingerprint_items:
        duration = min_duration
        while duration <= max_duration:
            resp = await search_acoustid(api_key, duration, fp_string)
            if resp.get("error"):
                await result_queue.put(("quit", None, None, None))
                return
            if resp.get("results"):
                await result_queue.put(("match", resp["results"], duration, offset))
                return
            duration += 5
            await asyncio.sleep(INTERVAL_DELAY)
        await result_queue.put(("done", None, None, None))


async def run_acoustid_parallel(
    file_path: str,
    api_keys: List[str],
    min_duration: int,
    max_duration: int
) -> Optional[Dict[str, Any]]:
    """
    1) Read TEMP_FOLDER/<basename>.json to get {"fingerprints": { offset: fp_str, ... }}
    2) Split those (offset,fp_str) pairs across api_keys (limited by MAX_CORES_ALLOWED).
    3) Launch one asyncio task per key. Wait until the first "match" appears in the queue,
       then cancel all tasks and return a dict containing:
       {
         "service": "MusicBrainz",
         "trackId": ...,
         "score": ...,
         "offset": ...,
         "duration": ...
       }
       Returns None if no match or if an invalid key is detected.
    """
    base = trim_extension(Path(file_path).name)
    json_path = TEMP_FOLDER / f"{base}.json"
    if not json_path.exists():
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    fingerprints: Dict[str, str] = data.get("fingerprints", {})
    items = [(int(k), v) for k, v in fingerprints.items()]
    if not items:
        return None

    num_keys = min(len(api_keys), MAX_CORES_ALLOWED)
    chunks = chunkify(items, num_keys)
    result_queue: asyncio.Queue = asyncio.Queue()

    tasks = []
    for i, key in enumerate(api_keys[:num_keys]):
        task = asyncio.create_task(
            _search_worker(key, chunks[i], min_duration, max_duration, result_queue)
        )
        tasks.append(task)

    while True:
        status, results_list, duration_val, offset_val = await result_queue.get()
        if status == "quit":
            for t in tasks:
                t.cancel()
            return None
        if status == "match":
            for t in tasks:
                t.cancel()
            best = results_list[0]
            return {
                "service": "MusicBrainz",
                "trackId": best.get("id"),
                "score": round(best.get("score", 0) * 100, 2),
                "offset": offset_val,
                "duration": duration_val,
            }
        if all(t.done() for t in tasks):
            break

    try:
        json_path.unlink()
    except Exception:
        pass

    return None
