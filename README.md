# Job Monitor

A free, daily pipeline that pulls new job postings matching your criteria from the Adzuna API, rule-filters them, and emails you a bucketed digest. No paid AI APIs involved — the smart triage and resume tailoring happens when you bring the keepers into a Claude chat.

## How it works

```
GitHub Actions (daily cron)
        ↓
  fetch_jobs.py  →  pulls jobs from Adzuna (free API, real salary data)
        ↓
  state.py        →  drops anything already seen
        ↓
  filter_jobs.py  →  scores each job 0-3 on salary, location, cluster fit
        ↓
  notify.py       →  emails you a digest bucketed Strong / Worth a look / Needs review
        ↓
  [you read it, pick keepers, bring them to Claude chat for fit-screening + resume]
```

Cost: **$0**. Adzuna free tier, GitHub Actions free tier, Gmail SMTP.

## One-time setup

### 1. Create the repository

1. On GitHub, create a new repo named `job-monitor` (public or private — doesn't matter).
2. **Do NOT** initialize it with a README — this project already has one.
3. On your machine, clone it (or download this zip and push the contents):
   ```bash
   git clone https://github.com/YOUR_USERNAME/job-monitor.git
   cd job-monitor
   # ... drop these files in ...
   git add .
   git commit -m "initial commit"
   git push
   ```

### 2. Get an Adzuna API key (free)

1. Go to https://developer.adzuna.com and register.
2. Create an application — gives you an `app_id` and `app_key`.
3. The free tier (250 calls/day) is plenty: this script uses ~6 calls per run.

### 3. Set up Gmail App Password

The digest emails are sent through your Gmail. You can't use your regular Gmail password — you need an App Password.

1. Enable 2-step verification on your Google account if you haven't: https://myaccount.google.com/security
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Pick "Mail" and "Other (Custom name)" — name it `job-monitor`. Copy the 16-character password it gives you.

### 4. Add secrets to GitHub

In your repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**. Add five secrets:

| Name              | Value                                              |
|-------------------|----------------------------------------------------|
| `ADZUNA_APP_ID`   | Your Adzuna app_id from step 2                     |
| `ADZUNA_APP_KEY`  | Your Adzuna app_key from step 2                    |
| `SMTP_USER`       | Your Gmail address (e.g. `you@gmail.com`)          |
| `SMTP_PASS`       | The 16-char App Password from step 3 (no spaces)   |
| `EMAIL_TO`        | Where the digest should land (often same as user)  |

### 5. Run it manually the first time

In your repo on GitHub: **Actions tab → Daily Job Scan → Run workflow** (button on the right). Watch the run logs.

If it completes green and you get an email — you're done. The daily schedule (12:00 UTC = 7:00 AM ET) will run from here on.

## Local testing (optional but recommended before pushing)

Before relying on the cloud run, you can test the pipeline locally:

```bash
# 1. Copy .env.example to .env and fill in real values
cp .env.example .env
# (edit .env with your Adzuna and Gmail values)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Load env and run
set -a; source .env; set +a
cd src
python main.py
```

You should see console output as it fetches, classifies, and emails. Check your inbox for the digest.

To test just the Adzuna fetch (no email):

```bash
cd src
python fetch_jobs.py
```

## Tuning

Almost everything tunable lives in `src/config.py`:

- **Salary floor** — `SALARY_MIN` (default 95,000)
- **Title clusters** — edit `TITLE_CLUSTERS` to add/remove search terms
- **Location radius** — `INDY_DISTANCE_KM` (default 64 km ≈ 40 miles)
- **Fake-remote red flags** — `FAKE_REMOTE_PATTERNS` (regex list)
- **CSM sales-component keywords** — `SALES_COMPONENT_KEYWORDS`

After editing, commit and push — the next run picks up the changes.

## The daily loop

1. **Morning** — digest email arrives. Three sections: Strong / Worth a look / Needs review.
2. **Skim** the Strong section first; click through promising titles to read full postings.
3. **For keepers**, open a Claude chat (or continue an existing one) and paste:
   > Here's a posting from my daily monitor. Screen it against my master resume — flavor (AI adoption/enablement vs MLOps vs implementation vs CSM-with-sales), real fit, any gaps. If it passes, draft a tailored resume.
   > 
   > [paste the posting]
4. Apply.

The script does the boring filtering for free. Claude does the judgment when it actually matters.

## Files

```
job-monitor/
├── .github/workflows/daily-job-scan.yml   # daily cron + commits state back
├── src/
│   ├── config.py          # all tunables
│   ├── fetch_jobs.py      # Adzuna API client
│   ├── state.py           # seen-jobs dedupe store
│   ├── filter_jobs.py     # rule-based classifier (the "brains")
│   ├── notify.py          # Gmail SMTP digest email
│   └── main.py            # orchestrator
├── data/
│   └── seen_jobs.json     # state, committed back by the workflow
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Troubleshooting

**The workflow runs but no email arrives.**
Check Spam. If still nothing, check the Actions run logs — SMTP errors print clearly. Most common cause: App Password typed with spaces, or 2FA not enabled on the Google account.

**Adzuna returns zero jobs.**
The `salary_min` filter combined with the title clusters may be too tight. Try lowering `SALARY_MIN` to 75,000 temporarily to confirm the pipeline works end-to-end, then put it back.

**Same jobs alerted twice.**
The state commit step in the workflow may have failed. Check the Actions logs for "no permission to push" — fix by going to **Settings → Actions → General → Workflow permissions** and selecting "Read and write permissions."

**A field name from Adzuna doesn't match.**
Adzuna occasionally tweaks response shape. Run `python src/fetch_jobs.py` locally and look at the raw response (add a `print(resp.json())` in `_query` temporarily). Fix the field name in `_normalize`.

## Future upgrades

If the manual paste-into-chat step starts feeling like a chore and you want full automation, you'd:

1. Get an Anthropic API key (https://console.anthropic.com).
2. Add a `screen_jobs.py` module that calls the API per job to do the flavor classification + fit score (replaces the manual chat step).
3. Add it to `main.py` between classify and notify.

That's the V2. Not worth doing until you've used the free version for a few weeks and identified what specifically annoys you about it.
