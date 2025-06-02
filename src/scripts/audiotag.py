# src/scripts/audiotag.py

import time
from typing import Any, Dict, Optional

import requests
from utils.consts import AUDIOTAG_ENDPOINT

# How many seconds of audio to upload (e.g. 180)
AUDIOTAG_DURATION = 180
# How long to wait between polls (in seconds)
AUDIOTAG_SLEEP = 0.5
# Maximum number of polling attempts before giving up
MAX_AUDIOTAG_ATTEMPTS = 50


class AudiotagResult:
    def __init__(self, match: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None):
        self.match = match
        self.error = error


def post_audiotag(data: Any, is_validating: bool = False, key: Optional[str] = None) -> Dict[str, Any]:
    """
    If `data` is a string, treat it as a token for "get_result";
    otherwise, `data` is a multipart/form-data payload for "identify".
    """
    if isinstance(data, str):
        # Polling request
        body = {
            "action": "get_result",
            "apikey": key,
            "token": data,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(AUDIOTAG_ENDPOINT, headers=headers, data=body, timeout=30)
    else:
        # Initial identify request (multipart/form-data)
        response = requests.post(AUDIOTAG_ENDPOINT, files=data, timeout=30)

    try:
        return response.json()
    except Exception:
        return {}


def search_with_audiotag(key: str, file_path: str) -> AudiotagResult:
    """
    Uploads `file_path` (first AUDIOTAG_DURATION seconds) to Audiotag.net.
    Polls until a match is found or until MAX_AUDIOTAG_ATTEMPTS is reached.
    Returns an AudiotagResult with `.match` set to the first found track dict, or None.
    """
    result = AudiotagResult(match=None, error=None)
    try:
        with open(file_path, "rb") as fp:
            files = {"file": (file_path, fp, "audio/mpeg")}
            data = {
                "action": "identify",
                "apikey": key,
                "start_time": "0",
                "time_len": str(AUDIOTAG_DURATION),
            }
            response = requests.post(AUDIOTAG_ENDPOINT, data=data, files=files, timeout=30)
            resp_json = response.json()
    except Exception as e:
        result.error = e
        return result

    if resp_json.get("success") != 1:
        return result

    # If job was found immediately
    if resp_json.get("job_status") == "found":
        tracks = resp_json.get("data", [{}])[0].get("tracks", [])
        if tracks:
            result.match = tracks[0]
            return result

    # Otherwise, poll until found or timed out
    token = resp_json.get("token")
    attempts = 0
    while attempts < MAX_AUDIOTAG_ATTEMPTS:
        time.sleep(AUDIOTAG_SLEEP)
        attempts += 1
        try:
            poll_json = post_audiotag(token, is_validating=False, key=key)
            status = poll_json.get("result")
            if status and status != "wait":
                if status == "found":
                    tracks = poll_json.get("data", [{}])[0].get("tracks", [])
                    if tracks:
                        result.match = tracks[0]
                break
        except Exception as e:
            result.error = e
            return result

    return result
