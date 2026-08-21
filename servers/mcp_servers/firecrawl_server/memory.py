"""The working-memory event log: append, fold, render.

The log is append-only. Updating a record means appending another record with the
same id carrying only the changed fields; `fold` merges them in order. Nothing is
ever rewritten, so a crash can never leave memory half-written.
"""

from __future__ import annotations

import json
from pathlib import Path

PREFIX = {"question": "q", "finding": "f", "note": "n"}
STATUSES = ("open", "resolved")


def read_records(path: Path) -> list[dict]:
    """Parse the log. A torn final line — a crash mid-write — is dropped rather
    than failing the whole read; anything torn earlier is real corruption."""
    if not path.exists():
        return []
    lines = [l for l in (raw.strip() for raw in path.read_text().splitlines()) if l]
    out = []
    for i, line in enumerate(lines):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                break
            raise
    return out


def fold(records: list[dict]) -> dict[str, dict[str, dict]]:
    """Merge the log into current state: {type: {id: record}}, in insertion order."""
    state: dict[str, dict[str, dict]] = {t: {} for t in PREFIX}
    for rec in records:
        bucket = state[rec["t"]]
        rec_id = rec["id"]
        if rec_id in bucket:
            bucket[rec_id].update(rec)
        else:
            bucket[rec_id] = dict(rec)
    return state


def _next_id(bucket: dict[str, dict], prefix: str) -> str:
    n = 0
    for rec_id in bucket:
        if rec_id.startswith(prefix) and rec_id[len(prefix) :].isdigit():
            n = max(n, int(rec_id[len(prefix) :]))
    return f"{prefix}{n + 1}"


def _validate(rec: dict, state: dict[str, dict[str, dict]], is_new: bool) -> None:
    t = rec["t"]
    if is_new:
        if t == "question" and not rec.get("text"):
            raise ValueError("a new question needs 'text'")
        if t == "finding":
            for field in ("q", "text", "url"):
                if not rec.get(field):
                    raise ValueError(f"a new finding needs '{field}'")
        if t == "note" and not rec.get("text"):
            raise ValueError("a new note needs 'text'")
    if t == "finding" and "q" in rec and rec["q"] not in state["question"]:
        raise ValueError(f"finding references unknown question {rec['q']!r}")
    if t == "question":
        status = rec.get("status")
        if status is not None and status not in STATUSES:
            raise ValueError(f"question status must be one of {STATUSES}, got {status!r}")


def _heal(path: Path) -> None:
    """Drop a torn trailing line before appending, so a crash mid-write can't
    strand a broken record in the middle of the log. The only rewrite we do."""
    if not path.exists():
        return
    lines = [l for l in (raw.strip() for raw in path.read_text().splitlines()) if l]
    if not lines:
        return
    try:
        json.loads(lines[-1])
    except json.JSONDecodeError:
        path.write_text("".join(line + "\n" for line in lines[:-1]))


def append(path: Path, records: list[dict]) -> list[str]:
    """Validate, assign ids to new records, append. Returns the ids touched.

    Validation runs over the whole batch before anything is written, so a bad
    record in the middle can't leave a partial batch on disk.
    """
    if not records:
        raise ValueError("no records given")

    state = fold(read_records(path))
    staged, ids = [], []

    for raw in records:
        rec = {k: v for k, v in raw.items() if v is not None}
        t = rec.get("t")
        if t not in PREFIX:
            raise ValueError(f"record type must be one of {tuple(PREFIX)}, got {t!r}")

        rec_id = rec.get("id")
        is_new = rec_id is None
        if is_new:
            rec_id = _next_id(state[t], PREFIX[t])
            rec["id"] = rec_id
            if t == "question":
                rec.setdefault("status", "open")
        elif rec_id not in state[t]:
            raise ValueError(f"no such {t} to update: {rec_id!r}")

        _validate(rec, state, is_new)

        # Make the new record visible to later records in the same batch, so a
        # question and its findings can be appended in one call.
        if rec_id in state[t]:
            state[t][rec_id].update(rec)
        else:
            state[t][rec_id] = dict(rec)

        staged.append(rec)
        ids.append(rec_id)

    _heal(path)
    with path.open("a") as fh:
        for rec in staged:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return ids


def render(meta: dict, records: list[dict], question_id: str | None = None) -> str:
    state = fold(records)
    questions, findings, notes = state["question"], state["finding"], state["note"]

    by_question: dict[str, list[dict]] = {}
    for finding in findings.values():
        by_question.setdefault(finding["q"], []).append(finding)

    def block(q: dict) -> list[str]:
        head = f"- [{q['id']}] {q['text']}"
        if q.get("status") == "resolved" and q.get("answer"):
            head += f" → {q['answer']}"
        lines = [head]
        for f in by_question.get(q["id"], []):
            lines.append(f"  - [{f['id']}] {f['text']} — {f['url']}")
        return lines

    if question_id is not None:
        if question_id not in questions:
            raise ValueError(f"no such question: {question_id!r}")
        return "\n".join(block(questions[question_id]))

    out = [f"# Objective\n{meta['objective']}", f"\n_{meta['credits']} credits used_"]
    for label, want in (("Open", "open"), ("Resolved", "resolved")):
        rows = [q for q in questions.values() if q.get("status", "open") == want]
        out.append(f"\n## {label}")
        out.extend(["\n".join(block(q)) for q in rows] or ["_none_"])
    if notes:
        out.append("\n## Notes")
        out.extend(f"- [{n['id']}] {n['text']}" for n in notes.values())
    return "\n".join(out)
