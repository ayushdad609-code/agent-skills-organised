#!/data/data/com.termux/files/usr/bin/python3
"""
auto-build.py — Reads project prompts from Google Sheets, generates code via
Gemini 2.0 Flash, creates public GitHub repos, and updates the sheet.

Sheet columns: Date | Inspired By | Project Name | Project Prompt | Status | Repo Link | Error

Usage:
    python3 auto-build.py
"""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("auto-build")

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
SCRIPTS_DIR = os.path.expanduser("~/knowledge-base/scripts")
ENV_PATH = os.path.join(SCRIPTS_DIR, ".env.supabase")
SHEET_NAME = "github new project"

# Column header → 0-based index (we also derive them at runtime)
COL_HEADERS = [
    "Date",
    "Inspired By",
    "Project Name",
    "Project Prompt",
    "Status",
    "Repo Link",
    "Error",
]

# ---------------------------------------------------------------------------
# 1. Load environment variables
# ---------------------------------------------------------------------------
def load_env(path: str) -> dict:
    """Parse a KEY=VALUE env file and set os.environ."""
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
            os.environ[key.strip()] = value.strip()
    return env


# ---------------------------------------------------------------------------
# 2. Import google-sheets helper
# ---------------------------------------------------------------------------
sys.path.insert(0, SCRIPTS_DIR)

# Rename-safe import: the module file is google-sheets.py (has hyphen)
import importlib

google_sheets = importlib.import_module("google-sheets")
get_client = google_sheets.get_client

# ---------------------------------------------------------------------------
# 3. GitHub username
# ---------------------------------------------------------------------------
def get_github_username() -> str:
    result = subprocess.run(
        ["gh", "api", "user", "-q", ".login"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get GitHub username: {result.stderr.strip()}")
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# 4. Gemini: generate project files
# ---------------------------------------------------------------------------
def call_gemini(prompt_text: str, api_key: str) -> str:
    """Call Gemini 2.0 Flash via REST API and return the text response."""
    import requests as _requests

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 65536},
    }

    # Retry up to 3 times with back-off for rate limits / transient errors
    for attempt in range(1, 4):
        try:
            resp = _requests.post(url, json=payload, timeout=120)
            if resp.status_code == 429:
                raise RuntimeError("Rate limited (429)")
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            if attempt == 3:
                raise
            wait = 2 ** attempt
            log.warning("Gemini attempt %d failed (%s), retrying in %ds…", attempt, exc, wait)
            time.sleep(wait)


def generate_project(prompt: str, api_key: str) -> dict:
    """Send the project prompt to Gemini and return {filepath: content}."""
    system_prompt = (
        "You are a senior software engineer. Generate a complete project based "
        "on this prompt:\n"
        f"{prompt}\n\n"
        "Return a JSON object where keys are file paths "
        "(e.g., 'src/main.py', 'README.md', '.gitignore') and values are the "
        "full file contents. Include at minimum: README.md, .gitignore, and all "
        "source files. Make the code production-quality."
    )

    text = call_gemini(system_prompt, api_key).strip()

    # Strip markdown code fences if present (```json ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        files = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {exc}\n---\n{text[:500]}")

    if not isinstance(files, dict) or not files:
        raise ValueError(f"Expected non-empty dict, got {type(files).__name__}")

    return files


# ---------------------------------------------------------------------------
# 5. Create repo, write files, push
# ---------------------------------------------------------------------------
def create_and_push_repo(
    repo_name: str, files: dict, github_user: str
) -> str:
    """Create a GitHub repo, write files, commit & push. Return repo URL."""
    tmp_parent = tempfile.mkdtemp(prefix="auto-build-")

    try:
        clone_dir = os.path.join(tmp_parent, repo_name)

        # Create remote repo + local clone
        result = subprocess.run(
            ["gh", "repo", "create", repo_name, "--public", "--clone"],
            capture_output=True,
            text=True,
            cwd=tmp_parent,
        )
        if result.returncode != 0:
            raise RuntimeError(f"gh repo create failed: {result.stderr.strip()}")

        if not os.path.isdir(clone_dir):
            # Fallback: gh may have cloned to a slightly different name
            dirs = [
                d for d in os.listdir(tmp_parent)
                if os.path.isdir(os.path.join(tmp_parent, d))
            ]
            if dirs:
                clone_dir = os.path.join(tmp_parent, dirs[0])
            else:
                raise RuntimeError("Clone directory not found after gh repo create")

        # Write files
        for filepath, content in files.items():
            # Sanitise path — no leading slashes, no ..
            filepath = filepath.lstrip("/")
            if ".." in filepath:
                continue
            full = os.path.join(clone_dir, filepath)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w") as f:
                f.write(content)

        # Git add, commit, push
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        commit_msg = f"init: auto-generated from project prompt [{today}]"

        for cmd in [
            ["git", "add", "."],
            ["git", "commit", "-m", commit_msg],
            ["git", "push", "-u", "origin", "HEAD"],
        ]:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=clone_dir)
            if r.returncode != 0:
                raise RuntimeError(f"`{' '.join(cmd)}` failed: {r.stderr.strip()}")

        return f"https://github.com/{github_user}/{repo_name}"

    finally:
        # Clean up temp dir
        shutil.rmtree(tmp_parent, ignore_errors=True)


# ---------------------------------------------------------------------------
# 6. Slugify project name → repo name
# ---------------------------------------------------------------------------
def slugify(name: str) -> str:
    """Turn a project name into a valid GitHub repo name."""
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9\s\-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-") or "auto-project"


# ---------------------------------------------------------------------------
# 7. Update sheet cells
# ---------------------------------------------------------------------------
def update_row(ws, row_idx: int, status: str, repo_link: str = "", error: str = ""):
    """Update Status, Repo Link, Error columns for a given row.

    row_idx is 1-based (header = row 1, first data row = row 2).
    """
    headers = ws.row_values(1)
    col_status = headers.index("Status") + 1
    col_repo = headers.index("Repo Link") + 1
    col_error = headers.index("Error") + 1

    ws.update_cell(row_idx, col_status, status)
    ws.update_cell(row_idx, col_repo, repo_link)
    ws.update_cell(row_idx, col_error, error)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("=== auto-build.py started ===")

    # Load env
    env = load_env(ENV_PATH)
    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not found in %s", ENV_PATH)
        sys.exit(1)

    # GitHub user
    github_user = get_github_username()
    log.info("GitHub user: %s", github_user)

    # Open sheet
    gc = get_client()
    try:
        sh = gc.open(SHEET_NAME)
    except Exception:
        log.error("Could not open sheet '%s'", SHEET_NAME)
        sys.exit(1)

    ws = sh.sheet1
    records = ws.get_all_records()
    log.info("Found %d rows in '%s'", len(records), SHEET_NAME)

    if not records:
        log.info("No rows to process. Exiting.")
        return

    processed = 0
    skipped = 0

    for i, row in enumerate(records):
        # row_idx: header is row 1, first data row is row 2
        row_idx = i + 2

        project_name = str(row.get("Project Name", "")).strip()
        project_prompt = str(row.get("Project Prompt", "")).strip()
        status = str(row.get("Status", "")).strip()

        # Skip already-processed rows
        if status:
            skipped += 1
            continue

        if not project_prompt:
            log.warning("Row %d: empty Project Prompt, skipping", row_idx)
            skipped += 1
            continue

        repo_name = slugify(project_name) if project_name else slugify(project_prompt[:50])
        log.info("--- Processing row %d: %s (repo: %s) ---", row_idx, project_name or "(unnamed)", repo_name)

        try:
            # Generate code via Gemini
            log.info("Sending prompt to Gemini…")
            files = generate_project(project_prompt, api_key)
            log.info("Gemini returned %d file(s): %s", len(files), ", ".join(files.keys()))

            # Create repo & push
            log.info("Creating GitHub repo and pushing…")
            repo_url = create_and_push_repo(repo_name, files, github_user)
            log.info("✅ Repo created: %s", repo_url)

            # Update sheet: success
            update_row(ws, row_idx, status="✅", repo_link=repo_url)
            processed += 1

        except Exception as exc:
            error_msg = str(exc)[:200]  # Truncate for the cell
            log.error("❌ Row %d failed: %s", row_idx, exc)
            log.debug(traceback.format_exc())
            try:
                update_row(ws, row_idx, status="❌", error=error_msg)
            except Exception as update_exc:
                log.error("Failed to update sheet for row %d: %s", row_idx, update_exc)

        # Small delay to avoid API rate limits between projects
        time.sleep(2)

    log.info("=== Done. Processed: %d | Skipped: %d ===", processed, skipped)


if __name__ == "__main__":
    main()
