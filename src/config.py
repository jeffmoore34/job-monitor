"""
config.py — the one file you'll actually edit to tune the monitor.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEN_JOBS_PATH = ROOT / "data" / "seen_jobs.json"

SALARY_MIN = 95_000

INDY_LOCATION = "Indianapolis, Indiana"
INDY_DISTANCE_KM = 64
REMOTE_KEYWORDS = "remote"

# Each cluster is a list of EXACT PHRASES. The fetcher hits Adzuna once per
# phrase using `what_phrase` (exact-phrase match) — this avoids the noise from
# word-level OR matching across common words like "manager" or "AI".
TITLE_CLUSTERS = [
    {
        "name": "ai_enablement",
        "priority": 1,
        "title_phrases": [
            "AI enablement",
            "AI adoption",
            "AI implementation",
            "AI transformation",
            "AI deployment",
            "AI program manager",
            "AI solutions consultant",
            "AI adoption specialist",
            "AI consultant",
            "Copilot consultant",
            "Generative AI consultant",
            "GenAI consultant",
        ],
    },
    {
        "name": "implementation",
        "priority": 2,
        "title_phrases": [
            "implementation consultant",
            "implementation manager",
            "implementation lead",
            "implementation specialist",
            "onboarding lead",
            "onboarding manager",
            "professional services consultant",
            "deployment consultant",
            "solutions consultant",
        ],
    },
    {
        "name": "csm_with_sales",
        "priority": 3,
        "title_phrases": [
            "customer success manager",
            "customer success lead",
            "senior customer success",
            "customer onboarding manager",
            "customer onboarding specialist",
        ],
        "require_sales_component": True,
    },
]

MAX_DAYS_OLD = 2
RESULTS_PER_PAGE = 25

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

SALES_COMPONENT_KEYWORDS = [
    "expansion", "upsell", "up-sell", "cross-sell", "cross sell",
    "renewal", "quota", "revenue growth", "account growth",
    "book of business", "pipeline", "expansion revenue", "nrr", "grr",
]
