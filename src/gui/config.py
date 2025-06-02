# src/gui/config.py

import os
import sys
import platform
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parents[1] / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"

def scan_config():
    """Scan and return system info and relevant app paths."""
    # Try to find ffmpeg, yt-dlp, audfprint, etc.
    def which(name):
        from shutil import which as shwhich
        return shwhich(name) or ""

    data = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "app_version": "1.0.0",  # or dynamically insert
        "ffmpeg_path": which("ffmpeg"),
        "yt_dlp_path": which("yt-dlp"),
        "audfprint_path": str((Path(__file__).parents[2] / "scripts" / "audfprint" / "audfprint.py").resolve()),
        "default_data_dir": str((Path.home() / "WerZatSongData").resolve()),
        "first_launch": None,
        "config_version": 1,
    }
    return data

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        cfg = scan_config()
        save_config(cfg)
        return cfg
