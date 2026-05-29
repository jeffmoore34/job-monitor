"""
filter_jobs.py — rule-based classifier that buckets each new job by signal
strength so the email digest is scannable.

This is the deterministic layer. It does the 70% of judgment that's
mechanical (salary listed? remote real or HQ-tethered? CSM with sales
component?) and leaves the fuzzy 30% (true fit, AI-adoption vs MLOps flavor)
for you to handle when you bring keepers into Claude chat.

Each job is scored 0-3 across three checks and bucketed:
  3  -> strong   (worth a serious look)
  2  -> decent   (worth a look, one piece of uncertainty)
  0-1 -> review  (matches a cluster but has issues to verify)
"""

import re

import config

# Pre-compile patterns once for speed.
_FAKE_REMOTE_RES = [re.compile(p, re.IGNORECASE) for p in config.FAKE_REMOTE_PATTERNS]


def _find_fake_remote_signal(text):
    """Return the matched fake-remote phrase, or None."""
    for rx in _FAKE_REMOTE_RES:
        m = rx.search(text)
        if m:
            return m.group(0)
    return None


def _has_sales_component(text):
    """True if the description mentions sales/expansion ownership."""
    lower = text.lower()
    return any(kw in lower for kw in config.SALES_COMPONENT_KEYWORDS)


def _salary_signal(job):
    """Return (passes, note). Passes = salary is listed AND meets floor."""
    if job["salary_min"] and job["salary_min"] >= config.SALARY_MIN:
        return True, f"Salary listed: ${int(job['salary_min']):,}+"
    if job["salary_max"] and job["salary_max"] >= config.SALARY_MIN:
        return True, f"Salary range up to ${int(job['salary_max']):,}"
    if job["salary_min"] or job["salary_max"]:
        # Salary listed but below floor — Adzuna shouldn't return these given
        # the API-level filter, but guard anyway.
        return False, "Salary below $95K floor"
    return False, "Salary not listed — confirm before applying"


def _location_signal(job):
    """Return (passes, note). Passes = clean remote OR clean Indianapolis."""
    blob = f"{job['title']} {job['location']} {job['description']}".lower()
    indy_match = "indianapolis" in blob or "indiana" in (job["location"] or "").lower()
    remote_claimed = "remote" in blob or job["location_pass"] == "remote"
    fake_signal = _find_fake_remote_signal(job["description"])

    if indy_match and not fake_signal:
        return True, "Indianapolis area"
    if remote_claimed and not fake_signal:
        return True, "Reads as genuinely remote"
    if remote_claimed and fake_signal:
        return False, f"Claims remote but flags: '{fake_signal}'"
    if fake_signal:
        return False, f"Possible HQ-tethered: '{fake_signal}'"
    return False, "Location unclear — verify"


def _cluster_signal(job):
    """Return (passes, note). The CSM cluster requires a sales component."""
    if not job.get("require_sales_component"):
        return True, f"Cluster: {job['cluster']}"
    if _has_sales_component(job["description"]):
        return True, "CSM role with sales/expansion component"
    return False, "CSM role with no visible sales/expansion — verify"


def classify_job(job):
    """
    Return (bucket, signals, flags) for a job.

      bucket  : 'strong' | 'decent' | 'review'
      signals : list of positive notes (str)
      flags   : list of concerns        (str)
    """
    signals = []
    flags = []
    score = 0

    for check in (_salary_signal, _location_signal, _cluster_signal):
        passed, note = check(job)
        if passed:
            signals.append(note)
            score += 1
        else:
            flags.append(note)

    if score == 3:
        bucket = "strong"
    elif score == 2:
        bucket = "decent"
    else:
        bucket = "review"

    return bucket, signals, flags
