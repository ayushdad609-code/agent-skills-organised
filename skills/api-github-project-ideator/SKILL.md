---
name: github-project-ideator
description: Research GitHub trending repos to identify gaps and synthesize mega project prompts into the github new project Google Sheet.
origin: Custom
---

# GitHub Project Ideator

## When to Activate
- When the user wants to generate new project ideas based on current trends.
- User says "find new project ideas", "research github trending", or "run project ideator".

## Workflow
1. **Research**: Fetch the current GitHub Trending page (all languages, this week).
2. **Analyze**: For each repository, gather its core purpose, current limitations, missing features, and target users. Look for gaps (no mobile support, poor CLI UX, missing integrations, weak docs, etc.).
3. **Synthesize**: Construct one mega project prompt that directly solves the most compelling gap or unifies multiple ideas. The prompt must include Project name, Problem it solves, Core features, Tech stack suggestion, Unique angle, and a copy-paste-ready Build prompt.
4. **Report**: Append one row to the Google Sheet named `github new project` using the `knowledge-base/scripts/google-sheets.py` script. The columns are: `Date`, `Inspired By`, `Project Name`, `Project Prompt`.
