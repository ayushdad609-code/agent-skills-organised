---
name: autonomous-project-builder
description: Execute project prompts from the github new project Google Sheet by scaffolding and pushing new public GitHub repositories.
origin: Custom
---

# Autonomous Project Builder

## When to Activate
- When there are pending project prompts ready to be built in the Google Sheet.
- User says "build pending projects", "run project builder", or "execute project prompts".

## Workflow
1. **Fetch Pending Work**: Open the Google Sheet `github new project` using `knowledge-base/scripts/google-sheets.py`. Find all rows where the `Status` column is empty.
2. **Execute**: For each pending row, read the `Project Prompt` and:
   - Create a new public GitHub repository using the `Project Name` (via `gh` CLI or GitHub MCP).
   - Scaffold the full project structure (code, README.md, config files, .gitignore).
   - Commit and push all generated files with the message: `init: auto-generated from project prompt [YYYY-MM-DD]`.
3. **Report Back**: Update the Google Sheet row. Set `Status` to ✅ (and fill `Repo Link`) on success, or ❌ (and fill `Error` with a short reason) on failure.
