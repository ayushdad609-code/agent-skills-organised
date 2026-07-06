#!/data/data/com.termux/files/usr/bin/python3
"""
Auto-Repair — Reads unprocessed bugs/improvements from a Google Sheet buglist,
fetches file content from GitHub, sends to Gemini for a fix, commits the
corrected file, and updates the sheet with status + commit link.

Usage:
    python3 auto-repair.py [--dry-run] [--limit N]

Requires:
    - google-sheets.py in the same directory (for get_client)
    - gh CLI authenticated
    - GEMINI_API_KEY in .env.supabase
    - Google OAuth token configured via google-sheets-auth.py
"""

import os
import sys
import re
import base64
import json
import subprocess
import tempfile
import shutil
import time
import logging
import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Path setup — allow importing google-sheets.py as a module
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# google-sheets.py → importable as google_sheets (hyphen replaced)
import importlib
google_sheets = importlib.import_module("google-sheets")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("auto-repair")

# ---------------------------------------------------------------------------
# Load .env.supabase
# ---------------------------------------------------------------------------
ENV_FILE = os.path.join(SCRIPT_DIR, ".env.supabase")

if os.path.isfile(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    log.error("Missing GEMINI_API_KEY — set it in .env.supabase")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SPREADSHEET_NAME = "github buglist"
RATE_LIMIT_DELAY = 3  # seconds between items
MAX_CHANGE_RATIO = 0.50  # reject changes that alter >50% of the file
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, **kwargs):
    """Run a subprocess, return CompletedProcess. Logs on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        log.warning("Command failed: %s\nstderr: %s", " ".join(cmd), result.stderr.strip())
    return result


def get_github_username():
    """Get the authenticated GitHub username via gh CLI."""
    result = run(["gh", "api", "user", "-q", ".login"])
    if result.returncode != 0:
        log.error("Cannot determine GitHub user — is `gh` authenticated?")
        sys.exit(1)
    return result.stdout.strip()


def parse_finding(finding_text):
    """
    Parse the Finding column.
    Expected format:  'filepath:line description'
    Returns (filepath, line_number_or_none, description).
    """
    # Try  filepath:123 description
    m = re.match(r"^(.+?):(\d+)\s+(.+)$", finding_text.strip())
    if m:
        return m.group(1).strip(), m.group(2), m.group(3).strip()

    # Fallback:  filepath: description  (no line number)
    m = re.match(r"^(.+?):\s*(.+)$", finding_text.strip())
    if m:
        return m.group(1).strip(), None, m.group(2).strip()

    return None, None, finding_text.strip()


def fetch_file_from_github(owner, repo, filepath):
    """Fetch a file's content from GitHub via gh CLI and base64-decode it."""
    result = run([
        "gh", "api",
        f"repos/{owner}/{repo}/contents/{filepath}",
        "-q", ".content",
    ])
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    try:
        return base64.b64decode(raw).decode("utf-8")
    except Exception as e:
        log.error("base64 decode failed for %s: %s", filepath, e)
        return None


def call_gemini(prompt):
    """Call Gemini API and return the text response."""
    import requests

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 65536,
        },
    }
    for attempt in range(3):
        try:
            resp = requests.post(GEMINI_URL, json=payload, timeout=120)
            if resp.status_code == 429:
                wait = (attempt + 1) * 10
                log.warning("Gemini rate-limited, retrying in %ds…", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            log.error("Gemini returned no content: %s", json.dumps(data)[:500])
            return None
        except requests.exceptions.RequestException as e:
            log.error("Gemini request error (attempt %d): %s", attempt + 1, e)
            if attempt < 2:
                time.sleep(5)
    return None


def similarity_ratio(a, b):
    """Return 0.0–1.0 similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def strip_markdown_fences(text):
    """Remove wrapping ```lang ... ``` fences if Gemini adds them anyway."""
    text = text.strip()
    # Remove opening fence
    text = re.sub(r"^```\w*\n?", "", text)
    # Remove closing fence
    text = re.sub(r"\n?```\s*$", "", text)
    return text


def commit_message_for(finding_type, summary, filepath):
    """Build a commit message following conventional-commit style."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prefix = "fix" if finding_type.lower() in ("bug", "error", "vulnerability") else "improve"
    short = summary[:72] if len(summary) > 72 else summary
    return f"{prefix}: {short} — auto-resolved from buglist [{today}]"


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def process_row(row, row_index, ws, gh_user, dry_run=False):
    """
    Process a single buglist row.
    row: dict from sheet (keys = header names)
    row_index: 1-based sheet row (header = row 1, first data = row 2)
    ws: gspread worksheet object for updates
    """
    finding = row.get("Finding", "").strip()
    repo_full = row.get("Repo", "").strip()          # e.g. owner/repo
    finding_type = row.get("Type", "bug").strip()     # bug / improvement

    if not finding or not repo_full:
        log.warning("Row %d: missing Finding or Repo, skipping", row_index)
        return

    if "/" not in repo_full:
        log.info("Row %d: Repo '%s' has no owner, assuming current user '%s'", row_index, repo_full, gh_user)
        owner = gh_user
        repo = repo_full
    else:
        owner, repo = repo_full.split("/", 1)
    filepath, line_no, description = parse_finding(finding)

    if not filepath:
        log.warning("Row %d: Could not parse filepath from Finding, skipping", row_index)
        update_status(ws, row_index, row, "❌", error="Could not parse filepath from Finding")
        return

    log.info("Row %d: %s/%s → %s — %s", row_index, owner, repo, filepath, description[:60])

    # --- Fetch file content ---
    file_content = fetch_file_from_github(owner, repo, filepath)
    if file_content is None:
        msg = f"Could not fetch {filepath} from {repo_full}"
        log.error("Row %d: %s", row_index, msg)
        update_status(ws, row_index, row, "❌", error=msg)
        return

    # --- Call Gemini ---
    prompt = (
        f"You are a senior software engineer. Fix this {finding_type} in the file "
        f"'{filepath}' from repo '{repo}':\n\n"
        f"Issue: {finding}\n\n"
        f"Current file content:\n```\n{file_content}\n```\n\n"
        f"Return ONLY the complete corrected file content, nothing else. "
        f"No markdown fences, no explanation — just the fixed code."
    )

    if dry_run:
        log.info("Row %d: [DRY RUN] Would call Gemini and commit fix for %s", row_index, filepath)
        return

    fixed_content = call_gemini(prompt)
    if fixed_content is None:
        update_status(ws, row_index, row, "❌", error="Gemini returned no response")
        return

    fixed_content = strip_markdown_fences(fixed_content)

    # --- Safety check: change magnitude ---
    ratio = similarity_ratio(file_content, fixed_content)
    change_pct = (1 - ratio) * 100
    log.info("Row %d: Change magnitude: %.1f%%", row_index, change_pct)

    if ratio < MAX_CHANGE_RATIO:
        msg = f"Change too large ({change_pct:.0f}%), needs manual review"
        log.warning("Row %d: %s", row_index, msg)
        update_status(ws, row_index, row, "❌", error=msg)
        return

    # --- Clone, write, commit, push ---
    tmpdir = tempfile.mkdtemp(prefix="auto-repair-")
    try:
        clone_result = run(["gh", "repo", "clone", f"{owner}/{repo}", tmpdir])
        if clone_result.returncode != 0:
            update_status(ws, row_index, row, "❌", error=f"Clone failed: {clone_result.stderr[:120]}")
            return

        target_path = os.path.join(tmpdir, filepath)
        if not os.path.isfile(target_path):
            update_status(ws, row_index, row, "❌", error=f"File {filepath} not found in cloned repo")
            return

        # Write fixed content
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        # Commit
        msg = commit_message_for(finding_type, description, filepath)
        run(["git", "config", "user.name", gh_user], cwd=tmpdir)
        run(["git", "config", "user.email", f"{gh_user}@users.noreply.github.com"], cwd=tmpdir)
        run(["git", "add", filepath], cwd=tmpdir)

        # Check if there's actually a diff
        diff_check = run(["git", "diff", "--cached", "--quiet"], cwd=tmpdir)
        if diff_check.returncode == 0:
            log.info("Row %d: No changes detected after fix — file already correct", row_index)
            update_status(ws, row_index, row, "✅", commit_url="(no change needed)")
            return

        commit_result = run(["git", "commit", "-m", msg], cwd=tmpdir)
        if commit_result.returncode != 0:
            update_status(ws, row_index, row, "❌", error=f"Commit failed: {commit_result.stderr[:120]}")
            return

        push_result = run(["git", "push"], cwd=tmpdir)
        if push_result.returncode != 0:
            update_status(ws, row_index, row, "❌", error=f"Push failed: {push_result.stderr[:120]}")
            return

        # Get commit URL
        log_result = run(
            ["git", "log", "-1", "--format=%H"],
            cwd=tmpdir,
        )
        commit_sha = log_result.stdout.strip()
        commit_url = f"https://github.com/{owner}/{repo}/commit/{commit_sha}"
        log.info("Row %d: ✅ Committed → %s", row_index, commit_url)

        update_status(ws, row_index, row, "✅", commit_url=commit_url)

    except Exception as e:
        log.exception("Row %d: Unexpected error", row_index)
        update_status(ws, row_index, row, "❌", error=str(e)[:200])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def update_status(ws, row_index, row, status, commit_url=None, error=None):
    """Update the Status, Commit Link, and Error columns in the sheet."""
    try:
        headers = ws.row_values(1)
        header_map = {h: i + 1 for i, h in enumerate(headers)}  # 1-based col index

        if "Status" in header_map:
            ws.update_cell(row_index, header_map["Status"], status)

        if commit_url and "Commit Link" in header_map:
            ws.update_cell(row_index, header_map["Commit Link"], commit_url)

        if error and "Error" in header_map:
            ws.update_cell(row_index, header_map["Error"], error)

    except Exception as e:
        log.error("Row %d: Failed to update sheet: %s", row_index, e)


def main():
    parser = argparse.ArgumentParser(description="Auto-repair bugs from GitHub buglist sheet")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--limit", type=int, default=0, help="Max items to process (0 = all)")
    args = parser.parse_args()

    log.info("🔧 Auto-Repair starting%s", " [DRY RUN]" if args.dry_run else "")

    # --- GitHub user ---
    gh_user = get_github_username()
    log.info("GitHub user: %s", gh_user)

    # --- Open spreadsheet ---
    gc = google_sheets.get_client()
    try:
        sh = gc.open(SPREADSHEET_NAME)
    except Exception as e:
        log.error("Cannot open spreadsheet '%s': %s", SPREADSHEET_NAME, e)
        sys.exit(1)

    ws = sh.sheet1
    all_rows = ws.get_all_records()
    log.info("📊 Loaded %d rows from '%s'", len(all_rows), SPREADSHEET_NAME)

    # --- Filter unprocessed ---
    unprocessed = []
    for i, row in enumerate(all_rows):
        sheet_row = i + 2  # row 1 = header, data starts at row 2
        status = str(row.get("Status", "")).strip()
        if not status:
            unprocessed.append((sheet_row, row))

    log.info("🔍 %d unprocessed finding(s)", len(unprocessed))
    if not unprocessed:
        log.info("Nothing to do — all rows have a Status.")
        return

    if args.limit > 0:
        unprocessed = unprocessed[: args.limit]
        log.info("Limiting to %d item(s)", args.limit)

    # --- Process each ---
    processed = 0
    for idx, (sheet_row, row) in enumerate(unprocessed):
        process_row(row, sheet_row, ws, gh_user, dry_run=args.dry_run)
        processed += 1

        # Rate-limit delay between items (skip after last)
        if idx < len(unprocessed) - 1:
            log.info("⏳ Waiting %ds before next item…", RATE_LIMIT_DELAY)
            time.sleep(RATE_LIMIT_DELAY)

    log.info("✅ Done — processed %d item(s)", processed)


if __name__ == "__main__":
    main()
