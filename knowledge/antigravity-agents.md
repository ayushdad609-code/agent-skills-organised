# AGENTS.md — Antigravity CLI Agent Config
# Used by Claude Code, Codex, and compatible agent frameworks

## Project Overview

**Antigravity CLI** is a modular AI-agent workspace that merges:
- A curated skill library (`.agents/skills/`)
- A git-native API client (`docs/api/`)
- A safety enforcement layer (always active)
- Gemini CLI extensions (`config/extensions/`)
- Codebase graph maps (`codebase-maps/`)

## Entrypoints

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Primary config (Claude Code) |
| `AGENTS.md` | This file — agent-framework config |
| `config/GEMINI.md` | Gemini CLI system prompt |
| `.agents/skills/*/SKILL.md` | Individual skill definitions |

## Agent Roles

### Researcher Agent
- Invoked via: `$agent-researcher` or skill trigger
- Config: `.agents/skills/agent-researcher/SKILL.md`
- Hooks: memory store/search, pre/post task logging

### Safety Agent (passive, always active)
- Script: `.agents/skills/ai-safety-layer/scripts/safety_check.py`
- Audit log: `ai_safety_audit.log`

## Memory System

```bash
# Store context
memory_store "key_$(date +%s)" "value"

# Search stored context
memory_search "key_*" | head -5
```

## Conventions

- All skills use YAML frontmatter with `name:` and `description:` fields
- Scripts live in `<skill>/scripts/`
- Reference docs live in `<skill>/references/`
- Templates live in `<skill>/templates/`
- API requests live in `docs/api/<name>.md`

## Environment Variables

Set these before using any skill that requires external APIs:

```bash
# Example — fill in your own values
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""
export GITHUB_TOKEN=""
export INSTAGRAM_ACCESS_TOKEN=""
export FIRECRAWL_API_KEY=""
export PENPOT_API_TOKEN=""
export GEMINI_API_KEY=""
```

All `{{VAR_NAME}}` placeholders in skill files and API docs are resolved
from the current shell environment at runtime.
