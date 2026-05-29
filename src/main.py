"""
main.py — orchestrator. Runs the full daily pipeline:

    fetch → dedupe → classify → email → save state

Designed to be called as:  python -m src.main  (from repo root)
or              :  python src/main.py
"""

import sys
from datetime import datetime, timezone

import config
import fetch_jobs
import filter_jobs
import notify
import state


def main():
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{started}] Job Monitor starting.")

    # ---- 1. Fetch ----
    print("Fetching jobs from Adzuna...")
    all_jobs = fetch_jobs.fetch_all()
    print(f"  Adzuna returned {len(all_jobs)} unique postings across clusters.")

    # ---- 2. Dedupe ----
    seen = state.load_seen()
    new_jobs = state.filter_new(all_jobs, seen)
    print(f"  {len(new_jobs)} are new since last run.")

    if not new_jobs:
        print("Nothing new. Exiting cleanly.")
        return 0

    # ---- 3. Classify ----
    for j in new_jobs:
        bucket, signals, flags = filter_jobs.classify_job(j)
        j["bucket"] = bucket
        j["signals"] = signals
        j["flags"] = flags

    buckets = {
        "strong": [j for j in new_jobs if j["bucket"] == "strong"],
        "decent": [j for j in new_jobs if j["bucket"] == "decent"],
        "review": [j for j in new_jobs if j["bucket"] == "review"],
    }
    print(
        f"  Buckets — strong: {len(buckets['strong'])},"
        f" decent: {len(buckets['decent'])},"
        f" review: {len(buckets['review'])}"
    )

    # ---- 4. Notify ----
    print("Sending digest email...")
    notify.send_digest(buckets, len(new_jobs))
    print("  Sent.")

    # ---- 5. Save state ----
    state.mark_seen(new_jobs, seen)
    state.save_seen(seen)
    print(f"  State saved to {config.SEEN_JOBS_PATH}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
