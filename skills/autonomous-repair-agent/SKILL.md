---
name: autonomous-repair-agent
description: Execute real fixes directly in GitHub repositories based on pending bug reports and improvement findings from the github buglist Google Sheet.
origin: Custom
---

# Autonomous Repair Agent

## When to Activate
- When there are pending bugs or improvements to be fixed in the Google Sheet.
- User says "fix pending bugs", "run repair agent", or "resolve buglist".

## Workflow
1. **Fetch Pending Work**: Open the Google Sheet `github buglist` using `knowledge-base/scripts/google-sheets.py`. Find all rows where the `Status` column is empty.
2. **Execute the Fix**: For each pending row, read the Repo, Type, and Finding:
   - Navigate to the correct file and location in the repository.
   - For **Bugs**: diagnose the root cause and implement a correct, minimal fix.
   - For **Improvements**: implement cleanly, respecting existing code style and architecture.
   - Commit message format: `fix: [summary] — auto-resolved from buglist [YYYY-MM-DD]` or `improve: [summary] ...`
   - Push directly to the repository's default branch.
3. **Report Back**: Update the Google Sheet row. Set `Status` to ✅ (and fill `Commit Link`) on success, or ❌ (and fill `Error` with a short reason) on failure, ambiguity, or unsafe fixes.
