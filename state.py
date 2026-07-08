"""Tracks which Drive files have already been uploaded, plus a per-day
counter so the daily safety cap is enforced across scheduler runs."""
import json
import os
from datetime import datetime, timezone


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"uploaded": {}, "daily": {}}


def save(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, path)


def already_uploaded(state, file_id):
    return file_id in state.get("uploaded", {})


def uploads_today(state):
    return state.get("daily", {}).get(_today(), 0)


def record_upload(state, file_id, file_name, video_id):
    state.setdefault("uploaded", {})[file_id] = {
        "name": file_name,
        "video_id": video_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    daily = state.setdefault("daily", {})
    daily[_today()] = daily.get(_today(), 0) + 1
    return state
