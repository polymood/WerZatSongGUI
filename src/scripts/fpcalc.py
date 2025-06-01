# src/scripts/fpcalc.py

import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Tuple, List

from scripts.consts import FFMPEG_COMMAND, FILLER_FILE, MUSICBRAINZ_LIMIT, TEMP_FOLDER, FPCALC_COMMAND
from scripts.helpers import trim_extension


def extend_file(original_file: str, offset: int) -> str:
    """
    If offset == 0, copy original_file to TEMP_FOLDER/<basename>-0.mp3.
    Otherwise, prepend a filler clip to shift the audio by `offset` seconds,
    then trim to MUSICBRAINZ_LIMIT seconds. Returns path to the extended file.
    """
    orig = Path(original_file)
    base = trim_extension(orig.name)
    dest = TEMP_FOLDER / f"{base}-{offset}.mp3"

    if offset == 0:
        dest.write_bytes(orig.read_bytes())
        return str(dest)

    cmd = [
        FFMPEG_COMMAND,
        "-i", str(FILLER_FILE),
        "-i", str(original_file),
        "-filter_complex",
        (
            f"[0:a]atrim=0:{offset},asetpts=PTS-STARTPTS[trimmed];"
            f"[trimmed][1:a]concat=n=2:v=0:a=1[concat];"
            f"[concat]atrim=0:{MUSICBRAINZ_LIMIT},asetpts=PTS-STARTPTS[final]"
        ),
        "-map", "[final]",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        "-ar", "44100",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(dest)


def calculate_fingerprint_for_offset(args: Tuple[str, int]) -> Tuple[int, str]:
    """
    Given (file_path, offset), create an extended clip, run fpcalc to get JSON,
    parse the fingerprint, then delete the extended file. Return (offset, fingerprint_str).
    """
    original_file, offset = args
    extended = extend_file(original_file, offset)

    cmd = [
        FPCALC_COMMAND,
        "-length", str(MUSICBRAINZ_LIMIT),
        "-json",
        extended,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        Path(extended).unlink()
        return offset, ""

    try:
        out_json = json.loads(proc.stdout)
        fingerprint = out_json.get("fingerprint", "")
    except json.JSONDecodeError:
        fingerprint = ""

    Path(extended).unlink()
    return offset, fingerprint


def calculate_fingerprints_for_file(file_path: str, extension: int) -> Dict[int, str]:
    """
    For `file_path`, generate fingerprints at offsets 0..extension.
    Returns a dict { offset: fingerprint_str, ... } and writes TEMP_FOLDER/<basename>.json.
    """
    tasks: List[Tuple[str, int]] = [(file_path, ofs) for ofs in range(extension + 1)]
    result_map: Dict[int, str] = {}

    max_workers = min(extension + 1, 8)  # match MAX_CORES_ALLOWED
    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        future_to_offset = {
            exe.submit(calculate_fingerprint_for_offset, task): task[1] for task in tasks
        }
        for future in as_completed(future_to_offset):
            ofs = future_to_offset[future]
            try:
                offset_val, fp_str = future.result()
                if fp_str:
                    result_map[offset_val] = fp_str
            except Exception:
                continue

    base = trim_extension(Path(file_path).name)
    outpath = TEMP_FOLDER / f"{base}.json"
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump({"fingerprints": result_map}, f)

    return result_map
