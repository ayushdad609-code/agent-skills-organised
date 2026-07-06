---
name: jules-orchestrator
description: Coordinate large-scale software engineering tasks with the Jules AI agent. Use when delegating background coding tasks (refactoring, bug fixes, dependency updates) to Jules while maintaining architectural oversight and validation.
---

# Jules Orchestrator

This skill enables a high-efficiency coordination pattern between Gemini CLI (The Leader) and Jules (The Background Agent).

## Core Coordination Pattern

1. **Strategic Planning (Leader)**: Analyze the codebase, identify dependencies, and break the large task into discrete, high-certainty sub-tasks suitable for Jules.
2. **Delegation (Leader -> Jules)**: Use the `git-api-client` to trigger a Jules session for each sub-task.
3. **Asynchronous Parallelism**: While Jules works on background PRs, the Leader handles complex architectural decisions or high-stakes logic.
4. **Validation & Integration (Leader)**: Use the `ai-safety-layer` and project test suites to verify Jules's PRs before merging.

## Workflows

### 1. Identify Jules-Ready Tasks
Jules excels at tasks with clear starting/ending states and minimal architectural ambiguity:
- Batch refactoring (e.g., "Rename this prop in all components")
- Dependency updates
- Implementing unit tests for existing logic
- Boilerplate generation
- Targeted bug fixes with reproduction steps

### 2. Delegate to Jules
Trigger a session using the `jules-create-session` contract in `docs/devex/api-contracts/`.

**Requirements:**
- **Source ID**: Get this from `jules-list-sources.md`.
- **Prompt**: Be specific. Include file paths and desired outcomes.

```bash
# Example Delegation
python3 .agents/skills/git-api-client/scripts/execute_api_request.py docs/devex/api-contracts/jules-create-session.md --env prompt="Refactor all components in src/ui to use the new ThemeProvider" source="github/user/repo"
```

### 3. Monitor and Validate
- **Monitor**: Check Jules's progress via the Jules Web UI or list activities via API.
- **Review**: Once Jules opens a PR, checkout the branch locally.
- **Validate**:
  1. Run `python3 .agents/skills/ai-safety-layer/scripts/safety_check.py` on the changes.
  2. Execute the project's test suite.
  3. Verify architectural alignment.

## Reference Materials

- **API Contracts**: `docs/devex/api-contracts/jules-*`
- **Secrets**: Jules API key is stored in the project's private memory (`secrets.md`).

## Best Practices

- **One Task, One Session**: Avoid giving Jules broad, multi-step goals. Break them down.
- **Context is King**: Provide Jules with relevant file paths in the prompt to reduce its discovery time.
- **Leader Final Approval**: Never merge a Jules PR without local validation.
