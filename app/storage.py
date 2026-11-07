"""JSON-file persistence with atomic writes and per-lesson locks.

Every stage writes only its own keys through update(), so a failure in one
stage can never clobber saved work or instructor edits from another.
"""
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from .config import get_settings

STAGES = ["research", "synthesis", "qc1", "qc2"]
MAX_VERSIONS = 60

_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _lock(lesson_id: str) -> threading.RLock:
    with _locks_guard:
        return _locks.setdefault(lesson_id, threading.RLock())


def _path(lesson_id: str):
    if not lesson_id.isalnum():
        raise KeyError(lesson_id)
    d = get_settings().data_dir
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{lesson_id}.json"


def _blank_stage() -> dict:
    return {"status": "pending", "error": None, "warnings": [], "attempts": 0,
            "started_at": None, "finished_at": None}


DEFAULTS = {"level": "intermediate", "prerequisites": "", "mode": "self_study",
            "usage": {}, "provenance": {}, "link_check": None}
LEVELS = ("beginner", "intermediate", "advanced")
MODES = ("self_study", "instructor_led")


def create(title: str, objective: str, level: str = "intermediate", prerequisites: str = "",
           mode: str = "self_study") -> dict:
    lesson_id = uuid.uuid4().hex[:10]
    rec = {
        "id": lesson_id, "title": title, "objective": objective,
        "level": level if level in LEVELS else "intermediate",
        "prerequisites": prerequisites.strip(), "mode": mode if mode in MODES else "self_study",
        "usage": {}, "provenance": {}, "link_check": None,
        "created_at": now(), "updated_at": now(),
        "stages": {s: _blank_stage() for s in STAGES},
        "sources": [], "research_meta": {},
        "generated": "", "content": "", "content_edited": False,
        "pending_generation": None,
        "versions": [], "qc": {"qc1": None, "qc2": None},
    }
    with _lock(lesson_id):
        _write(lesson_id, rec)
    return rec


def _write(lesson_id: str, rec: dict) -> None:
    p = _path(lesson_id)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    for attempt in range(6):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.05 * (attempt + 1))


def load(lesson_id: str) -> dict:
    p = _path(lesson_id)
    if not p.exists():
        raise KeyError(lesson_id)
    with _lock(lesson_id):
        rec = json.loads(p.read_text(encoding="utf-8"))
    for k, v in DEFAULTS.items():  # records written by older versions
        rec.setdefault(k, dict(v) if isinstance(v, dict) else v)
    return rec


def update(lesson_id: str, fn: Callable[[dict], None]) -> dict:
    with _lock(lesson_id):
        rec = load(lesson_id)
        fn(rec)
        rec["updated_at"] = now()
        _write(lesson_id, rec)
        return rec


def delete(lesson_id: str) -> None:
    p = _path(lesson_id)
    with _lock(lesson_id):
        if not p.exists():
            raise KeyError(lesson_id)
        p.unlink()
    with _locks_guard:
        _locks.pop(lesson_id, None)


def list_all() -> list[dict]:
    d = get_settings().data_dir
    if not d.exists():
        return []
    out = []
    for p in d.glob("*.json"):
        try:
            with _lock(p.stem):
                r = json.loads(p.read_text(encoding="utf-8"))
            out.append({"id": r["id"], "title": r["title"], "objective": r["objective"],
                        "updated_at": r["updated_at"],
                        "stages": {k: v["status"] for k, v in r["stages"].items()}})
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return sorted(out, key=lambda r: r["updated_at"], reverse=True)


def snapshot(rec: dict, label: str) -> None:
    """Append a version of the working content (mutates rec; call inside update())."""
    if rec["versions"] and rec["versions"][-1]["content"] == rec["content"]:
        return
    n = (rec["versions"][-1]["n"] + 1) if rec["versions"] else 1
    rec["versions"].append({"n": n, "ts": now(), "label": label, "content": rec["content"]})
    del rec["versions"][:-MAX_VERSIONS]


def recover_interrupted() -> None:
    """Stages left 'running' by a crashed/stopped server become failed (retryable)."""
    for item in list_all():
        def fix(rec):
            for st in rec["stages"].values():
                if st["status"] == "running":
                    st["status"] = "failed"
                    st["error"] = "Interrupted (server restarted). Retry this step."
        update(item["id"], fix)
