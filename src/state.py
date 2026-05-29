"""
state.py — remembers which jobs you've already been told about.

Without this you'd get re-pinged for the same posting every day. The store is
a small JSON file mapping job id -> date first seen. In GitHub Actions the
workflow commits this file back to the repo after each run so state persists
across runs (see .github/workflows/daily-job-scan.yml).
"""

import json
from datetime import date

import config


def load_seen():
    """Return the dict of seen-job-ids; empty dict if missing or corrupt."""
    path = config.SEEN_JOBS_PATH
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable state shouldn't crash the run; start fresh.
        return {}


def save_seen(seen):
    """Write seen-job-ids to disk, creating parent dirs if needed."""
    path = config.SEEN_JOBS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, sort_keys=True)


def filter_new(jobs, seen):
    """Return only jobs whose id is NOT in `seen`."""
    return [j for j in jobs if j["id"] not in seen]


def mark_seen(jobs, seen):
    """Record `jobs` as seen-today in the `seen` dict (mutates and returns)."""
    today = date.today().isoformat()
    for j in jobs:
        seen[j["id"]] = today
    return seen
