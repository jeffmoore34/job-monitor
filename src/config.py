"""
config.py — the one file you'll actually edit to tune the monitor.

WHAT to look for, HOW to judge it, lives here. The rest of the code reads
from this and shouldn't need touching.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS — absolute, computed from this file's location so the script works
# regardless of where you run it from.
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SEEN_JOBS_PATH = ROOT / "data" / "seen_jobs.json"

# ---------------------------------------------------------------------------
# SALARY FLOOR
# ---------------------------------------------------------------------------
# Hard minimum. Adzuna enforces this at the API level where salary data exists.
# Postings with no listed salary still come through (and get flagged in the
# digest as "salary not listed") rather than being dropped — better to surface
# and let you decide than miss good jobs that simply don't post comp.
SALARY_MIN = 95_000

# ---------------------------------------------------------------------------
# LOCATIONS
# ---------------------------------------------------------------------------
# Two passes per cluster: one geo-anchored on Indianapolis, one for remote.
# Adzuna distance is in KILOMETERS (so ~64 km ≈ 40 mi covers the metro and
# suburbs like Whitestown/Carmel).
INDY_LOCATION = "Indianapolis, Indiana"
INDY_DISTANCE_KM = 64

# Adzuna's US feed has no clean "remote" flag, so we do a keyword pass.
# The fake-remote detector below catches HQ-tethered postings.
REMOTE_KEYWORDS = "remote"

# ---------------------------------------------------------------------------
# TITLE CLUSTERS  (priority 1 = highest)
# ---------------------------------------------------------------------------
# Each cluster runs as its own Adzuna `what_or` query (any term can match).
# Keep clusters separate so relevance stays high and you can tune one without
# disturbing the others.
TITLE_CLUSTERS = [
    {
        "name": "ai_enablement",
        "priority": 1,
        "what_or": (
            "AI enablement AI adoption AI implementation AI transformation "
            "AI deployment AI program manager AI solutions consultant "
            "AI adoption specialist Copilot consultant"
        ),
    },
    {
        "name": "implementation",
        "priority": 2,
        "what_or": (
            "implementation consultant implementation manager onboarding lead "
            "professional services consultant deployment consultant "
            "solutions consultant implementation specialist"
        ),
    },
    {
        "name": "csm_with_sales",
        "priority": 3,
        "what_or": (
            "customer success manager senior customer success "
            "customer onboarding specialist"
        ),
        # Lowest-priority cluster; filter step looks for an explicit
        # sales/expansion component and flags pure-support CSM roles.
        "require_sales_component": True,
    },
]

# Days back to scan on each run. Daily schedule with a 2-day window gives a
# small safety overlap if a run is skipped.
MAX_DAYS_OLD = 2

# Results per cluster per location pass (Adzuna page size).
RESULTS_PER_PAGE = 25

# ---------------------------------------------------------------------------
# FAKE-REMOTE DETECTION
# ---------------------------------------------------------------------------
# Regex patterns (case-insensitive) that suggest a "remote" posting is
# actually HQ-tethered. The filter step flags these — it doesn't drop them,
# since some matter (e.g. hybrid-Indianapolis still works for you) and you'll
# want to see and judge.
FAKE_REMOTE_PATTERNS = [
    r"must (be )?(located|reside|live) in",
    r"within \d+\s*(miles|mi)\b",
    r"\bhybrid\b",
    r"\d+\s*days?\s*(per|a|in)\s*(week|the office)",
    r"\bin[-\s]?office\b",
    r"\bonsite\b",
    r"\bon[-\s]?site\b",
    r"commutable",
    r"must be (based|located) in (?!the\s+(us|united states))",
]

# ---------------------------------------------------------------------------
# CSM SALES-COMPONENT KEYWORDS
# ---------------------------------------------------------------------------
# For the csm_with_sales cluster only: signals that the role actually involves
# revenue ownership, not just support.
SALES_COMPONENT_KEYWORDS = [
    "expansion", "upsell", "up-sell", "cross-sell", "cross sell",
    "renewal", "quota", "revenue growth", "account growth",
    "book of business", "pipeline", "expansion revenue", "nrr", "grr",
]
