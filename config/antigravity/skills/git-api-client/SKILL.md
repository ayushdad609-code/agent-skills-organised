---
name: git-api-client
description: Offline-first, Git-native API client for executing and testing API requests stored as Markdown files. Use when you need to interact with APIs, document endpoints, or verify contract compliance without using heavy external tools like Postman.
---

# Git-Native API Client

This skill allows you to manage API requests as repository-native Markdown files. This ensures that API documentation and test cases live alongside the code, are version-controlled, and can be reviewed via standard Pull Request workflows.

## Workflow

1.  **Identify or Create Request File**: API requests are stored in `.md` files (e.g., `docs/api/get-users.md`).
2.  **Define Request Structure**:
    - Use YAML frontmatter for `method`, `url`, and `headers`.
    - Place the request body (JSON, text, etc.) below the frontmatter.
    - Support for environment variables using `{{VAR_NAME}}` syntax.
3.  **Execute Request**: Run the `execute_api_request.py` script to perform the call and see the response.

## File Format Example

```markdown
---
method: POST
url: https://jsonplaceholder.typicode.com/posts
headers:
  Content-Type: application/json; charset=UTF-8
---

{
  "title": "foo",
  "body": "bar",
  "userId": 1
}
```

## Tools & Scripts

- **`scripts/execute_api_request.py`**: The primary execution engine.
  - **Usage**: `python .agents/skills/git-api-client/scripts/execute_api_request.py <path_to_file>`
  - **Environment Variables**: The script automatically substitutes `{{ENV_VAR}}` with values from the current shell environment.

## Best Practices

- **Repository Structure**: Store API requests in a dedicated folder like `docs/api/` or `tests/integration/api/`.
- **Security**: Never hardcode secrets in the Markdown files. Use `{{API_TOKEN}}` and ensure the token is set in the environment or a `.env` file (which should be in `.gitignore`).
- **Responses**: When verifying an API, consider appending the response to a sibling `.response.md` file for record-keeping during development.
