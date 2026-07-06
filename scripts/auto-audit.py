#!/data/data/com.termux/files/usr/bin/python3
"""
auto-audit.py — Automated GitHub Codebase Auditor

Scans every public (non-archived, non-empty) GitHub repo, sends source code
to Gemini 2.0 Flash for review, deduplicates against existing findings in
the 'github buglist' Google Sheet, and appends new rows.

Designed to run unattended via cron on Termux.
"""

import base64
import importlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import date

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("auto-audit")

# ── Paths & constants ───────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.expanduser("~/knowledge-base/scripts")
ENV_PATH = os.path.join(SCRIPTS_DIR, ".env.supabase")
SHEET_NAME = "github buglist"
MAX_FILES_PER_REPO = 10
GEMINI_DELAY_SECS = 2
TODAY = date.today().isoformat()

SOURCE_EXTENSIONS = {
    "py", "js", "ts", "tsx", "jsx", "go", "java", "rs", "sh", "bash",
    "rb", "c", "cpp", "h", "hpp", "cs", "swift", "kt", "kts", "scala",
    "lua", "pl", "pm", "r", "sql", "tf", "hcl", "yaml", "yml", "toml",
    "dockerfile", "makefile",
}

SKIP_DIRS = {"node_modules", ".git", "vendor", "dist", "build",
             "__pycache__", ".venv", "venv", ".tox", ".mypy_cache"}


# ── 1. Load environment variables ───────────────────────────────────────────
def load_env(path: str) -> dict:
    """Parse KEY=VALUE lines from *path* into os.environ and return them."""
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                os.environ[key] = value
                env[key] = value
    except FileNotFoundError:
        log.error("Env file not found: %s", path)
        sys.exit(1)
    return env


# ── 2. GitHub helpers ────────────────────────────────────────────────────────
def gh_run(args: list[str], description: str = "") -> str | None:
    """Run a `gh` CLI command and return stdout, or None on failure."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        log.warning("gh %s failed: %s", description or " ".join(args[:3]),
                     result.stderr.strip())
        return None
    return result.stdout.strip()


def list_repos() -> list[dict]:
    """Return list of public repos [{name, isArchived, isEmpty}, …]."""
    raw = gh_run(
        ["repo", "list", "--json", "name,isArchived,isEmpty", "--limit", "100"],
        description="repo list",
    )
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("Failed to parse repo list JSON: %s", exc)
        return []


def get_owner() -> str:
    """Get the authenticated GitHub username."""
    raw = gh_run(["api", "user", "-q", ".login"], description="get owner")
    if not raw:
        log.error("Could not determine GitHub username")
        sys.exit(1)
    return raw.strip()


def get_file_tree(owner: str, repo: str) -> list[str]:
    """Return list of blob paths from the repo's HEAD tree."""
    raw = gh_run(
        ["api", f"repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
         "-q", '.tree[] | select(.type=="blob") | .path'],
        description=f"tree {repo}",
    )
    if not raw:
        return []
    return raw.splitlines()


def fetch_file_content(owner: str, repo: str, path: str) -> str | None:
    """Fetch and base64-decode a single file from the GitHub API."""
    raw = gh_run(
        ["api", f"repos/{owner}/{repo}/contents/{path}", "-q", ".content"],
        description=f"content {repo}/{path}",
    )
    if not raw:
        return None
    try:
        # GitHub returns base64 with possible newlines
        return base64.b64decode(raw.replace("\n", "")).decode("utf-8", errors="replace")
    except Exception as exc:
        log.warning("Base64 decode failed for %s/%s: %s", repo, path, exc)
        return None


# ── 3. File filtering ───────────────────────────────────────────────────────
def is_source_file(path: str) -> bool:
    """Return True if the path is a source-code file we care about."""
    parts = path.lower().split("/")
    # Skip anything inside ignored directories
    if any(d in SKIP_DIRS for d in parts[:-1]):
        return False
    basename = parts[-1]
    # Handle extensionless Makefile / Dockerfile
    if basename in ("makefile", "dockerfile"):
        return True
    ext = basename.rsplit(".", 1)[-1] if "." in basename else ""
    return ext in SOURCE_EXTENSIONS


def select_files(paths: list[str]) -> list[str]:
    """Filter and cap the list of source files."""
    selected = [p for p in paths if is_source_file(p)]
    return selected[:MAX_FILES_PER_REPO]


# ── 4. Gemini review ────────────────────────────────────────────────────────
def build_prompt(repo_name: str, code_blocks: dict[str, str]) -> str:
    """Assemble the review prompt with all code blocks."""
    code_section = ""
    for filepath, content in code_blocks.items():
        code_section += f"\n### {filepath}\n```\n{content}\n```\n"

    return (
        f"You are a senior code reviewer. Review this codebase from repo "
        f"'{repo_name}':\n{code_section}\n\n"
        "Identify specific Bugs and Improvements. For each finding, provide:\n"
        "- Type: 'Bug' or 'Improvement'\n"
        "- Finding: specific description including filename:line_number\n\n"
        'Return as JSON array: [{"type": "Bug", "finding": "filename:line description"}]'
    )


def call_gemini(prompt: str, api_key: str, retries: int = 3) -> str | None:
    """Call Gemini 2.0 Flash via REST API and return the text response."""
    import requests as _requests

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }

    for attempt in range(1, retries + 1):
        try:
            resp = _requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            log.warning("Gemini attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                backoff = GEMINI_DELAY_SECS * attempt
                log.info("Retrying in %ds…", backoff)
                time.sleep(backoff)
    return None


def parse_findings(raw_text: str) -> list[dict]:
    """Extract the JSON array of findings from Gemini's response."""
    if not raw_text:
        return []
    # Try to find a JSON array in the response (may be wrapped in ```json…```)
    match = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if not match:
        log.warning("No JSON array found in Gemini response")
        return []
    try:
        data = json.loads(match.group())
        # Validate structure
        return [
            {"type": item.get("type", "Unknown"), "finding": item.get("finding", "")}
            for item in data
            if isinstance(item, dict) and item.get("finding")
        ]
    except json.JSONDecodeError as exc:
        log.warning("JSON parse error in Gemini response: %s", exc)
        return []


# ── 5. Google Sheets integration ────────────────────────────────────────────
def get_sheets_module():
    """Import google-sheets.py as a module."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    spec = importlib.util.spec_from_file_location(
        "google_sheets", os.path.join(SCRIPTS_DIR, "google-sheets.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_existing_findings(gs_mod) -> set[tuple[str, str]]:
    """Return set of (Repo, Finding) already in the sheet."""
    existing = set()
    try:
        gc = gs_mod.get_client()
        sh = gc.open(SHEET_NAME)
        ws = sh.sheet1
        rows = ws.get_all_records()
        for row in rows:
            existing.add((str(row.get("Repo", "")), str(row.get("Finding", ""))))
        log.info("Loaded %d existing findings from sheet", len(existing))
    except Exception as exc:
        log.warning("Could not read existing sheet data (may not exist yet): %s", exc)
    return existing


def ensure_sheet_exists(gs_mod):
    """Create the sheet + header if it doesn't exist yet."""
    try:
        gc = gs_mod.get_client()
        gc.open(SHEET_NAME)
        log.info("Sheet '%s' already exists", SHEET_NAME)
    except Exception:
        log.info("Creating sheet '%s'…", SHEET_NAME)
        gc = gs_mod.get_client()
        sh = gc.create(SHEET_NAME)
        ws = sh.sheet1
        ws.append_row(["Date", "Repo", "Type", "Finding", "Status", "Commit Link", "Error"])
        log.info("Sheet created with header row")


def append_findings(gs_mod, rows: list[list]):
    """Append rows via the google-sheets helper."""
    if not rows:
        log.info("No new findings to append")
        return
    gs_mod.append_rows(SHEET_NAME, rows)
    log.info("Appended %d new finding(s) to '%s'", len(rows), SHEET_NAME)


# ── 6. Main orchestration ───────────────────────────────────────────────────
def audit_repo(owner: str, repo_name: str, api_key: str) -> list[dict]:
    """Audit a single repo and return list of {type, finding} dicts."""
    log.info("── Scanning %s ──", repo_name)

    tree = get_file_tree(owner, repo_name)
    if not tree:
        log.info("  No file tree returned, skipping")
        return []

    files = select_files(tree)
    if not files:
        log.info("  No source files after filtering, skipping")
        return []

    log.info("  Fetching %d source file(s)…", len(files))
    code_blocks: dict[str, str] = {}
    for fpath in files:
        content = fetch_file_content(owner, repo_name, fpath)
        if content:
            code_blocks[fpath] = content

    if not code_blocks:
        log.info("  All file fetches failed, skipping")
        return []

    prompt = build_prompt(repo_name, code_blocks)
    log.info("  Calling Gemini (files: %d, prompt: ~%d chars)…",
             len(code_blocks), len(prompt))
    raw = call_gemini(prompt, api_key)
    findings = parse_findings(raw)
    log.info("  Gemini returned %d finding(s)", len(findings))
    return findings


def main():
    log.info("═══ auto-audit started ═══")

    # Load env
    env = load_env(ENV_PATH)
    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not set in %s", ENV_PATH)
        sys.exit(1)

    # GitHub owner
    owner = get_owner()
    log.info("GitHub user: %s", owner)

    # List repos
    repos = list_repos()
    if not repos:
        log.warning("No repos found — nothing to audit")
        return

    # Filter active repos
    active = [r for r in repos if not r.get("isArchived") and not r.get("isEmpty")]
    log.info("Found %d public repo(s), %d active (non-archived, non-empty)",
             len(repos), len(active))

    if not active:
        log.info("Nothing to audit")
        return

    # Google Sheets setup
    gs = get_sheets_module()
    ensure_sheet_exists(gs)
    existing = load_existing_findings(gs)

    # Audit each repo
    all_new_rows: list[list] = []
    for repo_info in active:
        repo_name = repo_info["name"]
        try:
            findings = audit_repo(owner, repo_name, api_key)
        except Exception as exc:
            log.error("Unexpected error auditing %s: %s", repo_name, exc)
            continue

        for f in findings:
            key = (repo_name, f["finding"])
            if key in existing:
                continue  # duplicate
            row = [
                TODAY,            # Date
                repo_name,        # Repo
                f["type"],        # Type
                f["finding"],     # Finding
                "",               # Status
                "",               # Commit Link
                "",               # Error
            ]
            all_new_rows.append(row)
            existing.add(key)  # prevent intra-run duplicates

        # Rate-limit between repos
        time.sleep(GEMINI_DELAY_SECS)

    # Append to sheet
    append_findings(gs, all_new_rows)
    log.info("═══ auto-audit finished — %d new finding(s) ═══", len(all_new_rows))


if __name__ == "__main__":
    main()
