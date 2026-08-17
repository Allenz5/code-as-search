"""Run directories, the active-run pointer, and credit accounting."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from .lock import guard, write_atomic

ROOT = Path(__file__).resolve().parent.parent.parent
SEARCH = ROOT / "search"
ACTIVE = SEARCH / ".active"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_run(objective: str) -> str:
    SEARCH.mkdir(exist_ok=True)
    run_id = f"{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(2)}"
    (SEARCH / run_id / "pages").mkdir(parents=True)
    (SEARCH / run_id / "memory.jsonl").touch()
    save_meta(
        run_id,
        {
            "id": run_id,
            "objective": objective,
            "credits": 0,
            "status": "active",
            "created": _now(),
        },
    )
    ACTIVE.write_text(run_id)
    return run_id


def active() -> str:
    if not ACTIVE.exists():
        raise RuntimeError("no active run — call research_start first")
    run_id = ACTIVE.read_text().strip()
    if not (SEARCH / run_id).is_dir():
        raise RuntimeError(f"active run {run_id!r} has no directory")
    return run_id


def set_active(run_id: str) -> None:
    if not (SEARCH / run_id).is_dir():
        raise RuntimeError(f"no such run: {run_id!r}")
    ACTIVE.write_text(run_id)


def run_dir(run_id: str | None = None) -> Path:
    return SEARCH / (run_id or active())


def memory_path(run_id: str | None = None) -> Path:
    return run_dir(run_id) / "memory.jsonl"


def load_meta(run_id: str | None = None) -> dict:
    return json.loads((run_dir(run_id) / "run.json").read_text())


def save_meta(run_id: str, meta: dict) -> None:
    write_atomic(SEARCH / run_id / "run.json", json.dumps(meta, indent=2))


def spend(credits: int, run_id: str | None = None) -> str:
    run_id = run_id or active()
    with guard(run_dir(run_id) / "run.json"):  # parallel explorers charge the same run
        meta = load_meta(run_id)
        meta["credits"] += int(credits or 0)
        save_meta(run_id, meta)
    return f"{meta['credits']} credits"
