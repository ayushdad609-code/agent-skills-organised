#!/data/data/com.termux/files/usr/bin/python3
"""
auto-ideation.py — Scrape GitHub trending repos, synthesize a mega-project
idea via Gemini, and log it to a Google Sheet.

Designed for unattended cron execution on Termux.
"""

import json
import logging
import os
import re
import sys
import time
from datetime import date

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("auto-ideation")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPTS_DIR = os.path.expanduser("~/knowledge-base/scripts")
ENV_FILE = os.path.join(SCRIPTS_DIR, ".env.supabase")
SHEET_NAME = "github new project"
TRENDING_URL = "https://github.com/trending?since=weekly"
GEMINI_MODEL = "gemini-2.0-flash"
MAX_REPOS = 25
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_env(path: str) -> dict:
    """Parse KEY=VALUE lines from a dotenv-style file."""
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    return env


def scrape_trending() -> list[dict]:
    """Scrape the GitHub weekly trending page and return repo metadata."""
    import requests
    from bs4 import BeautifulSoup

    log.info("Scraping %s", TRENDING_URL)
    headers = {"User-Agent": "Mozilla/5.0 (auto-ideation bot)"}
    resp = requests.get(TRENDING_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos: list[dict] = []

    for article in soup.select("article.Box-row")[:MAX_REPOS]:
        # Repo name (owner/name)
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        name = "/".join(
            part.strip() for part in h2.get_text(strip=False).split("/")
        ).strip()

        # Description
        p = article.select_one("p")
        desc = p.get_text(strip=True) if p else ""

        # Stars
        stars_el = article.select_one(
            "a[href$='/stargazers']"
        ) or article.select_one("span.d-inline-block.float-sm-right")
        stars = ""
        if stars_el:
            stars = stars_el.get_text(strip=True).replace(",", "")

        # Language
        lang_el = article.select_one("span[itemprop='programmingLanguage']")
        lang = lang_el.get_text(strip=True) if lang_el else "N/A"

        repos.append(
            {
                "name": name,
                "description": desc,
                "stars": stars,
                "language": lang,
            }
        )

    log.info("Extracted %d repos", len(repos))
    return repos


def build_prompt(repos: list[dict]) -> str:
    """Build the Gemini prompt from scraped repos."""
    repo_lines = []
    for i, r in enumerate(repos, 1):
        repo_lines.append(
            f"{i}. {r['name']} — ⭐ {r['stars']} | {r['language']}\n"
            f"   {r['description']}"
        )
    repos_text = "\n".join(repo_lines)

    return (
        "You are a senior AI researcher and product architect. "
        "Given these trending GitHub repos this week:\n"
        f"{repos_text}\n\n"
        "Analyze gaps (no mobile, poor UX, lack of AI, weak docs). "
        "Synthesize ONE mega project idea that solves a major gap. "
        'Return EXACTLY this JSON format:\n'
        '{"inspired_by": "repo1, repo2", "project_name": "Name", '
        '"project_prompt": "Full detailed build prompt for an AI agent '
        "to build this project. Include: problem, core features, tech "
        'stack, unique angle."}'
    )


def call_gemini(prompt: str, api_key: str) -> dict:
    """Send prompt to Gemini REST API and return parsed JSON."""
    import requests as req

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("Gemini request (attempt %d/%d)", attempt, MAX_RETRIES)
            resp = req.post(url, json=payload, timeout=120)
            resp.raise_for_status()

            data = resp.json()
            text = (
                data["candidates"][0]["content"]["parts"][0]["text"].strip()
            )
            log.info("Gemini raw response length: %d chars", len(text))

            # Strip markdown code fences if present
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

            return json.loads(text)

        except json.JSONDecodeError as e:
            log.warning("JSON parse error on attempt %d: %s", attempt, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise
        except Exception as e:
            log.warning("Gemini API error on attempt %d: %s", attempt, e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise


def append_to_sheet(idea: dict) -> None:
    """Append the idea as a new row in the Google Sheet."""
    # Import the google-sheets helper from the scripts directory
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)

    from importlib import import_module
    gs = import_module("google-sheets")

    today = date.today().isoformat()
    row = [
        today,                         # Date
        idea.get("inspired_by", ""),    # Inspired By
        idea.get("project_name", ""),   # Project Name
        idea.get("project_prompt", ""), # Project Prompt
        "",                             # Status
        "",                             # Repo Link
        "",                             # Error
    ]

    log.info("Appending row to sheet '%s'", SHEET_NAME)
    gs.append_rows(SHEET_NAME, [row])
    log.info("Row appended successfully")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("=== auto-ideation start ===")

    # 1. Load environment
    if not os.path.exists(ENV_FILE):
        log.error("Env file not found: %s", ENV_FILE)
        sys.exit(1)
    env = load_env(ENV_FILE)
    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not set in %s", ENV_FILE)
        sys.exit(1)

    # 2. Scrape trending repos
    try:
        repos = scrape_trending()
    except Exception as e:
        log.error("Failed to scrape trending repos: %s", e)
        try:
            append_error_row(str(e))
        except Exception:
            pass
        sys.exit(1)

    if not repos:
        log.error("No repos found on trending page")
        sys.exit(1)

    # 3. Build prompt and call Gemini
    prompt = build_prompt(repos)
    try:
        idea = call_gemini(prompt, api_key)
    except Exception as e:
        log.error("Gemini failed after retries: %s", e)
        try:
            append_error_row(str(e))
        except Exception:
            pass
        sys.exit(1)

    log.info(
        "Idea generated: %s (inspired by %s)",
        idea.get("project_name", "???"),
        idea.get("inspired_by", "???"),
    )

    # 4. Append to Google Sheet
    try:
        append_to_sheet(idea)
    except Exception as e:
        log.error("Failed to append to Google Sheet: %s", e)
        sys.exit(1)

    log.info("=== auto-ideation complete ===")


def append_error_row(error_msg: str) -> None:
    """Append a row with just the date and error message."""
    if SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, SCRIPTS_DIR)
    from importlib import import_module
    gs = import_module("google-sheets")

    today = date.today().isoformat()
    row = [today, "", "", "", "", "", error_msg[:500]]
    gs.append_rows(SHEET_NAME, [row])
    log.info("Error row appended to sheet")


if __name__ == "__main__":
    main()
