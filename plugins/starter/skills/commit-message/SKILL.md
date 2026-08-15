---
description: Write a well-formed git commit message for the currently staged changes. Use when the user asks for help writing a commit message or wants staged changes summarized as a commit.
---

# Commit Message

Write a commit message for the staged changes.

## Steps

1. Run `git diff --staged` to see what is staged. If nothing is staged, say so and stop.
2. Summarize the change in an imperative subject line of 50 characters or fewer (e.g. "Add retry logic to webhook delivery").
3. If the change needs context, add a blank line and a short body explaining *why* the change was made, wrapped at 72 characters.
4. Present the message to the user. Do not commit unless they ask you to.

## Quality bar

- One logical change per message; if the diff mixes unrelated changes, point that out and suggest splitting.
- No trailing period on the subject line.
- Prefer plain language over conventional-commit prefixes unless the repository's history already uses them (check `git log --oneline -10`).
