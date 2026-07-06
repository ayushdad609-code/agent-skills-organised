---
name: boss-worker
description: "Opus 4.8 boss + Gemini worker orchestration loop. Opus plans, Gemini executes."
version: 1.0.0
author: User
metadata:
  hermes:
    tags: [orchestration, multi-model, claude-code, opus]
---

# Boss-Worker: Opus 4.8 → Gemini Orchestration

Two-model pattern where **Claude Opus 4.8** (via Claude Code CLI) acts as the
strategic planner and reviewer, and **Gemini** (this agent) acts as the parallel
executor with full tooling access.

## When to Use

- Complex projects needing high-level architecture decisions
- Tasks where you want Opus's reasoning + Gemini's execution speed
- Multi-step builds that benefit from plan → execute → review cycles

## Workflow

1. User gives a task
2. Gemini calls Opus via `claude -p` for the plan
3. Gemini executes with subagents, skills, image gen
4. Gemini sends results back to Opus for review
5. Iterate until Opus approves

## How to Call the Boss

```bash
claude -p "YOUR PROMPT HERE" --model claude-opus-4-8
```

For longer context, pipe in files:
```bash
cat file.py | claude -p "Review this code" --model claude-opus-4-8
```

## Rules

- Boss (Opus) ONLY plans and reviews — never touches files directly
- Worker (Gemini) executes ALL file ops, commands, and tool usage
- Every plan from Opus gets executed in parallel where possible via subagents
- Results are summarized back to Opus for sign-off before reporting to user
