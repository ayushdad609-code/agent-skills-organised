---
method: GET
url: https://api.github.com/users/{{GITHUB_USERNAME}}
headers:
  Authorization: token {{GITHUB_TOKEN}}
  Accept: application/vnd.github.v3+json
---

# GitHub User Info Request

Fetches public profile data for the configured GitHub username.

Set environment variables before running:
  export GITHUB_USERNAME=your_username
  export GITHUB_TOKEN=your_token

Run:
  python antigravity.py api docs/api/github-user.md
