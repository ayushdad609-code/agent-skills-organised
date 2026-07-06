---
name: codebase-auditor
description: Perform a structured code audit for all public GitHub repositories and document findings in the github buglist Google Sheet.
origin: Custom
---

# Codebase Auditor

## When to Activate
- When the user wants to proactively audit their repositories for bugs and improvements.
- User says "run codebase audit", "find bugs in my repos", or "audit my github".

## Workflow
1. **Retrieve Repos**: Fetch all of the user's public GitHub repositories.
2. **Audit**: Review all files in the codebase in full. Identify and document:
   - **Bugs**: Logic errors, security vulnerabilities, unsafe API usage, exception handling gaps.
   - **Improvements**: Code quality issues, missing docs, performance bottlenecks, architecture weaknesses.
3. **Report**: Append one row per finding to the Google Sheet `github buglist` (via `knowledge-base/scripts/google-sheets.py`).
   - Columns: `Date`, `Repo`, `Type`, `Finding`.
   - Be specific (include filename and line number/function).
   - Do not repeat findings from previous runs.
   - Skip empty or archived repositories.
