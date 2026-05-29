"""
notify.py — sends the daily digest email via Gmail SMTP.

Uses standard library only (smtplib + email). Sends multipart text+HTML so it
renders nicely in modern clients but degrades gracefully in text-only ones.

Requires the Gmail account to have 2FA enabled and an App Password generated
at https://myaccount.google.com/apppasswords. Plain Gmail passwords won't work.
"""

import os
import smtplib
import ssl
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def send_digest(buckets, total_count):
    """Build and send the digest email. `buckets` is a dict bucket -> [jobs]."""
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    email_to = os.environ["EMAIL_TO"]

    today = date.today().isoformat()
    subject = _subject(buckets, total_count, today)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg.attach(MIMEText(_render_text(buckets, today), "plain", "utf-8"))
    msg.attach(MIMEText(_render_html(buckets, today), "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


# ---------------------------------------------------------------------------
# Subject line — front-loads the strong-bucket count
# ---------------------------------------------------------------------------

def _subject(buckets, total, today):
    strong = len(buckets.get("strong", []))
    if strong:
        return f"Job Monitor — {strong} strong + {total - strong} more ({today})"
    return f"Job Monitor — {total} new matches ({today})"


# ---------------------------------------------------------------------------
# Plain-text rendering (fallback for clients that don't render HTML)
# ---------------------------------------------------------------------------

def _render_text(buckets, today):
    lines = [f"Job Monitor digest — {today}", "=" * 50, ""]
    for label, key in (("STRONG MATCHES", "strong"),
                       ("WORTH A LOOK", "decent"),
                       ("NEEDS REVIEW", "review")):
        jobs = buckets.get(key, [])
        if not jobs:
            continue
        lines.append(f"{label} ({len(jobs)})")
        lines.append("-" * len(label))
        for j in jobs:
            lines.append(f"• {j['title']} — {j['company']}")
            lines.append(f"  {j['location']}  |  cluster: {j['cluster']}")
            for s in j["signals"]:
                lines.append(f"  + {s}")
            for f in j["flags"]:
                lines.append(f"  ! {f}")
            lines.append(f"  {j['url']}")
            lines.append("")
        lines.append("")
    lines.append("— Paste promising ones into Claude chat for fit-screening "
                 "and resume tailoring.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML rendering — minimal inline CSS so most clients render it cleanly
# ---------------------------------------------------------------------------

_CSS = """
  body { font-family: -apple-system, Helvetica, Arial, sans-serif;
         color: #222; max-width: 720px; margin: 0 auto; padding: 16px; }
  h1   { font-size: 18px; margin: 0 0 4px; }
  .sub { color: #666; font-size: 13px; margin-bottom: 24px; }
  h2   { font-size: 15px; margin: 28px 0 10px; padding-bottom: 4px;
         border-bottom: 1px solid #ddd; }
  .job { border-left: 3px solid #ccc; padding: 8px 0 8px 12px;
         margin-bottom: 16px; }
  .job.strong { border-left-color: #2a8c4a; }
  .job.decent { border-left-color: #d9a417; }
  .job.review { border-left-color: #888; }
  .title { font-weight: 600; font-size: 15px; }
  .meta  { color: #555; font-size: 13px; margin: 2px 0 6px; }
  .signal { color: #2a8c4a; font-size: 13px; margin: 2px 0; }
  .flag   { color: #b8860b; font-size: 13px; margin: 2px 0; }
  a       { color: #1a4eaa; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .foot   { color: #888; font-size: 12px; margin-top: 32px;
            border-top: 1px solid #eee; padding-top: 12px; }
"""


def _render_html(buckets, today):
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        f"<style>{_CSS}</style></head><body>",
        f"<h1>Job Monitor digest</h1>",
        f"<div class='sub'>{escape(today)}</div>",
    ]
    for label, key in (("Strong matches", "strong"),
                       ("Worth a look", "decent"),
                       ("Needs review", "review")):
        jobs = buckets.get(key, [])
        if not jobs:
            continue
        parts.append(f"<h2>{escape(label)} ({len(jobs)})</h2>")
        for j in jobs:
            parts.append(_render_job_html(j, key))
    parts.append(
        "<div class='foot'>Paste the promising ones into Claude chat for "
        "fit-screening and resume tailoring against your master resume.</div>"
    )
    parts.append("</body></html>")
    return "".join(parts)


def _render_job_html(j, bucket_key):
    title = escape(j["title"]) or "(untitled)"
    url = escape(j["url"])
    parts = [f"<div class='job {bucket_key}'>"]
    if url:
        parts.append(f"<div class='title'><a href='{url}'>{title}</a></div>")
    else:
        parts.append(f"<div class='title'>{title}</div>")
    parts.append(
        f"<div class='meta'>{escape(j['company'])} · "
        f"{escape(j['location'])} · cluster: {escape(j['cluster'])}</div>"
    )
    for s in j["signals"]:
        parts.append(f"<div class='signal'>+ {escape(s)}</div>")
    for f in j["flags"]:
        parts.append(f"<div class='flag'>! {escape(f)}</div>")
    parts.append("</div>")
    return "".join(parts)
