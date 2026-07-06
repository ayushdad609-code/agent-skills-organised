# ⚡ Antigravity CLI

> Your unified AI-agent workspace — skills, safety, API client, and config in one repo.

Merged from **SAFE_CLI_VAULT** + **Claude Code** conventions, wired together for
immediate use with any compatible AI CLI (Claude Code, Gemini CLI, OpenCode, etc.).

---

## Structure

```
antigravity-cli/
├── CLAUDE.md                    ← Master config (Claude Code)
├── AGENTS.md                    ← Agent-framework config (Codex, etc.)
├── antigravity.py               ← CLI entrypoint
├── .env.example                 ← All API key placeholders
├── ai_safety_audit.log          ← Auto-created by safety layer
│
├── .agents/
│   └── skills/                  ← 22 modular agent skills
│       ├── ai-safety-layer/     ← Runtime safety enforcement
│       ├── ai-workflow-automation/
│       ├── agentic-workflow-automation/
│       ├── agent-researcher/
│       ├── frontend-design/
│       ├── github-readme-generator/
│       ├── second-brain/
│       ├── research-idea-validator/
│       ├── penpot-uiux-design/
│       ├── git-api-client/      ← Git-native API testing
│       ├── snapshot-test-refactorer/
│       ├── strategy-planning/
│       ├── web-design-guidelines/
│       └── ... (22 total)
│
├── config/
│   ├── GEMINI.md                ← Gemini CLI system prompt
│   └── extensions/
│       ├── Stitch/              ← AI UI/UX design extension
│       └── google-workspace/    ← Calendar, Drive, Gmail
│
├── docs/
│   └── api/                     ← Git-native API request files
│       └── github-user.md
│
└── codebase-maps/               ← Graph-based codebase navigation
    └── GRAPH_REPORT.md
```

---

## Quick Start

```bash
# 1. Clone / enter the project
cd antigravity-cli

# 2. Set up your environment
cp .env.example .env
# Edit .env and fill in any API keys you'll use now
# (leave the rest blank — you can add them later)

# 3. List available skills
python antigravity.py skills

# 4. Load a skill
python antigravity.py skill github-readme-generator

# 5. Run a safety check before any risky command
python antigravity.py safe "rm -rf ./build"

# 6. Execute a git-native API request
export GITHUB_USERNAME=your_username
export GITHUB_TOKEN=your_token
python antigravity.py api docs/api/github-user.md

# 7. View the safety audit log
python antigravity.py audit
```

---

## Skills

| Skill | What It Does |
|-------|-------------|
| `ai-safety-layer` | Blocks dangerous bash/SQL commands, logs all checks |
| `ai-workflow-automation` | Content pipelines, approval workflows, AI orchestration |
| `agentic-workflow-automation` | MCP-based autonomous agents, multi-step task execution |
| `agent-researcher` | Deep code analysis, pattern recognition, dependency mapping |
| `frontend-design` | Production-grade React/HTML/CSS components |
| `github-readme-generator` | Auto-generates README files from code/context |
| `github-profile` | GitHub profile README generation |
| `git-api-client` | Git-native API testing via Markdown files |
| `second-brain` | Obsidian PKM, GTD, Zettelkasten workflows |
| `research-idea-validator` | Academic idea validation with rubrics |
| `penpot-uiux-design` | UI/UX design in Penpot (Figma alternative) |
| `snapshot-test-refactorer` | Replace brittle snapshot tests with targeted assertions |
| `strategy-planning` | OKR, roadmaps, prioritization frameworks |
| `web-design-guidelines` | Accessibility audit, UX compliance review |
| `campaign-planning` | Marketing campaign briefs |
| `find-skills` | Discover installable agent skills via npx skills |
| `firecrawl-lead-gen` | Web scraping + lead generation via Firecrawl |
| `instagram` / `instagram-automation` | Instagram content & automation |
| `penpot-uiux-design` | Full Penpot MCP setup & design workflows |
| `git-city-3d-github-visualization` | 3D GitHub codebase visualization |
| `create-readme` | Quick README generation |
| `readme-blueprint-generator` | README blueprint scaffolding |

---

## API Keys

API keys are **intentionally blank** — this vault is provider-agnostic. Set any
key you need in `.env` and it will be picked up via `{{VAR_NAME}}` substitution
in skill files and API request docs.

---

## Safety Layer

Every command suggestion is run through the safety layer automatically. For
explicit auditing in your own scripts:

```bash
python .agents/skills/ai-safety-layer/scripts/safety_check.py "your command here"
```

All results (PASSED and BLOCKED) are appended to `ai_safety_audit.log`.

---

## Claude Code / Gemini CLI Config

- **Claude Code** reads `CLAUDE.md` automatically when you open the project
- **Gemini CLI** reads `config/GEMINI.md`
- **OpenCode** and other agents use `AGENTS.md`

---

*Built on SAFE_CLI_VAULT · Organized for Antigravity CLI · June 2026*
