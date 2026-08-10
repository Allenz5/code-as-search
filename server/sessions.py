"""Registry and reaper for live interact sessions.

An interact session holds a real browser. The agent is asked to close one when it
is done, but the server guarantees it: every open session is recorded on disk, a
background thread stops anything older than the age limit, and orphans left by a
previous process are reaped at startup.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from .runs import SEARCH

REGISTRY = SEARCH / ".sessions.json"
MAX_AGE = 120.0
_lock = threading.Lock()


def _load() -> dict[str, dict]:
    if not REGISTRY.exists():
        return {}
    try:
        return json.loads(REGISTRY.read_text())
    except json.JSONDecodeError:
        return {}


def _save(sessions: dict[str, dict]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(sessions, indent=2))


def note_open(scrape_id: str, url: str) -> None:
    with _lock:
        sessions = _load()
        sessions.setdefault(scrape_id, {"url": url, "opened": time.time()})
        _save(sessions)


def note_closed(scrape_id: str) -> None:
    with _lock:
        sessions = _load()
        if sessions.pop(scrape_id, None) is not None:
            _save(sessions)


def age(scrape_id: str) -> float:
    entry = _load().get(scrape_id)
    return time.time() - entry["opened"] if entry else 0.0


def reap(client, max_age: float = MAX_AGE) -> list[str]:
    """Stop every session older than max_age. Returns the ids reaped."""
    with _lock:
        sessions = _load()
        stale = [sid for sid, e in sessions.items() if time.time() - e["opened"] > max_age]
        for sid in stale:
            try:
                client.interact_stop(sid)
            except Exception:
                pass  # already gone server-side; drop it either way
            sessions.pop(sid, None)
        if stale:
            _save(sessions)
    return stale


def start_reaper(client, max_age: float = MAX_AGE, interval: float = 15.0) -> None:
    reap(client, max_age=0.0)  # orphans from a previous process

    def loop():
        while True:
            time.sleep(interval)
            try:
                reap(client, max_age)
            except Exception:
                pass

    threading.Thread(target=loop, daemon=True).start()


def stop_all(client) -> None:
    with _lock:
        for sid in _load():
            try:
                client.interact_stop(sid)
            except Exception:
                pass
        _save({})
