#!/usr/bin/env python3
"""
Antigravity CLI — Main Entrypoint
Unified CLI wrapper that ties together all vault skills,
the safety layer, and the git-native API client.

Usage:
  python antigravity.py skill <skill-name>        # Load and print a skill
  python antigravity.py skills                     # List all available skills
  python antigravity.py safe <command>             # Run safety check on a command
  python antigravity.py api <request-file>         # Execute an API request
  python antigravity.py audit                      # Show safety audit log
  python antigravity.py env                        # Check env vars status
"""

import sys
import os
import subprocess
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / ".agents" / "skills"
SAFETY_SCRIPT = SKILLS_DIR / "ai-safety-layer" / "scripts" / "safety_check.py"
API_SCRIPT = SKILLS_DIR / "git-api-client" / "scripts" / "execute_api_request.py"
AUDIT_LOG = ROOT / "ai_safety_audit.log"
DOCS_API_DIR = ROOT / "docs" / "api"

# ── Helpers ──────────────────────────────────────────────────
def banner():
    print("\n⚡ Antigravity CLI\n")

def list_skills():
    """List all available skills with their descriptions."""
    banner()
    skills = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    print(f"{'Skill':<35} {'Description'}")
    print("-" * 80)
    for skill_dir in skills:
        skill_md = skill_dir / "SKILL.md"
        desc = "(no description)"
        if skill_md.exists():
            with open(skill_md) as f:
                for line in f:
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"')
                        # Truncate long descriptions
                        if len(desc) > 60:
                            desc = desc[:57] + "..."
                        break
        print(f"  {skill_dir.name:<33} {desc}")
    print()

def load_skill(name: str):
    """Print a skill's SKILL.md content."""
    skill_md = SKILLS_DIR / name / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Skill '{name}' not found in {SKILLS_DIR}")
        print("Run 'python antigravity.py skills' to see available skills.")
        sys.exit(1)
    banner()
    print(f"📦 Skill: {name}\n")
    print(skill_md.read_text())

def run_safety_check(command: str):
    """Run the AI safety layer check on a command string."""
    if not SAFETY_SCRIPT.exists():
        print(f"❌ Safety script not found at {SAFETY_SCRIPT}")
        sys.exit(1)
    result = subprocess.run(
        [sys.executable, str(SAFETY_SCRIPT), command],
        capture_output=False
    )
    sys.exit(result.returncode)

def execute_api(request_file: str):
    """Execute a git-native API request from a Markdown file."""
    # Resolve relative to docs/api if no path given
    p = Path(request_file)
    if not p.exists():
        p = DOCS_API_DIR / request_file
    if not p.exists():
        print(f"❌ Request file not found: {request_file}")
        print(f"   Also tried: {DOCS_API_DIR / request_file}")
        sys.exit(1)
    if not API_SCRIPT.exists():
        print(f"❌ API script not found at {API_SCRIPT}")
        sys.exit(1)
    result = subprocess.run(
        [sys.executable, str(API_SCRIPT), str(p)],
        capture_output=False
    )
    sys.exit(result.returncode)

def show_audit():
    """Display the safety audit log."""
    if not AUDIT_LOG.exists():
        print("📋 No audit log found. Run a safety check first.")
        return
    print(f"📋 Audit Log ({AUDIT_LOG})\n")
    print(AUDIT_LOG.read_text()[-4000:])  # Show last ~4KB

def check_env():
    """Check which environment variables are set vs missing."""
    banner()
    env_example = ROOT / ".env.example"
    if not env_example.exists():
        print("❌ .env.example not found")
        return
    print(f"{'Variable':<35} {'Status'}")
    print("-" * 50)
    with open(env_example) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line or not line:
                continue
            key = line.split("=")[0]
            val = os.environ.get(key, "")
            status = "✅ set" if val else "⚠️  not set"
            print(f"  {key:<33} {status}")
    print()

# ── Main Dispatch ────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd in ("skills", "list"):
        list_skills()
    elif cmd == "skill" and len(sys.argv) >= 3:
        load_skill(sys.argv[2])
    elif cmd in ("safe", "safety", "check") and len(sys.argv) >= 3:
        run_safety_check(" ".join(sys.argv[2:]))
    elif cmd == "api" and len(sys.argv) >= 3:
        execute_api(sys.argv[2])
    elif cmd == "audit":
        show_audit()
    elif cmd == "env":
        check_env()
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
