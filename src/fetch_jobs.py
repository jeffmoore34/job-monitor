"""
fetch_jobs.py — pulls postings from the Adzuna API.

Adzuna is used because it has a legitimate public API, real salary data, and a
free tier. We do NOT scrape LinkedIn/Indeed (against their terms and brittle).

For each title cluster we run two passes: one anchored on Indianapolis (with a
distance radius) and one keyword pass for remote roles. Results are merged and
de-duplicated by Adzuna's job id before being returned.
"""

import os
import time
import requests

import config

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/us/search/1"


def _adzuna_credentials():
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise RuntimeError(
            "Missing ADZUNA_APP_ID / ADZUNA_APP_KEY. "
            "Register free at https://developer.adzuna.com and set them as env "
            "vars (locally) or repository secrets (GitHub Actions)."
        )
    return app_id, app_key


def _query(params):
    """Single Adzuna call with basic retry/backoff on transient errors."""
    app_id, app_key = _adzuna_credentials()
    full = {
        "app_id": app_id,
        "app_key": app_key,
        "content-type": "application/json",
        "results_per_page": config.RESULTS_PER_PAGE,
        "max_days_old": config.MAX_DAYS_OLD,
        "salary_min": config.SALARY_MIN,
        "sort_by": "date",
        **params,
    }
    for attempt in range(3):
        resp = requests.get(ADZUNA_BASE, params=full, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        if resp.status_code in (429, 500, 502, 503):
            time.sleep(2 * (attempt + 1))
            continue
        # Anything else (auth, malformed query) — fail loudly.
        resp.raise_for_status()
    return []


def _normalize(raw, cluster, location_pass):
    """Flatten Adzuna's nested shape into the dict the rest of the app expects."""
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")
    return {
        "id": str(raw.get("id")),
        "title": (raw.get("title") or "").strip(),
        "company": (raw.get("company") or {}).get("display_name", "Unknown"),
        "location": (raw.get("location") or {}).get("display_name", ""),
        "salary_min": float(salary_min) if salary_min is not None else None,
        "salary_max": float(salary_max) if salary_max is not None else None,
        "salary_is_predicted": str(raw.get("salary_is_predicted", "")) == "1",
        "description": raw.get("description", "") or "",
        "url": raw.get("redirect_url", ""),
        "created": raw.get("created", ""),
        "cluster": cluster["name"],
        "cluster_priority": cluster["priority"],
        "require_sales_component": cluster.get("require_sales_component", False),
        "location_pass": location_pass,  # "indianapolis" or "remote"
    }


def fetch_all():
    """Return a de-duplicated list of normalized job dicts across all clusters."""
    seen_ids = set()
    jobs = []

    for cluster in config.TITLE_CLUSTERS:
        # Pass 1: Indianapolis + radius
        indy = _query({
            "what_or": cluster["what_or"],
            "where": config.INDY_LOCATION,
            "distance": config.INDY_DISTANCE_KM,
        })
        # Pass 2: remote keyword
        remote = _query({
            "what_or": cluster["what_or"] + " " + config.REMOTE_KEYWORDS,
            "where": config.REMOTE_KEYWORDS,
        })

        for raw, location_pass in (
            [(r, "indianapolis") for r in indy]
            + [(r, "remote") for r in remote]
        ):
            jid = str(raw.get("id"))
            if jid in seen_ids:
                continue
            seen_ids.add(jid)
            jobs.append(_normalize(raw, cluster, location_pass))

    return jobs


if __name__ == "__main__":
    # Quick local test:  python src/fetch_jobs.py
    found = fetch_all()
    print(f"Fetched {len(found)} unique postings.")
    for j in found[:10]:
        salary = (
            f"${int(j['salary_min']):,}+" if j["salary_min"]
            else "salary not listed"
        )
        print(f"  [{j['cluster']}] {j['title']} — {j['company']} "
              f"({j['location']}, {salary})")
