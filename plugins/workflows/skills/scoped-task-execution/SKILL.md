---
description: Execute a single issue or ticket as a tightly scoped task — deliver the smallest correct change that satisfies the stated acceptance criteria, without expanding into cleanup, redesign, migration, refactoring, or adjacent fixes. Use whenever implementing a specific issue, ticket, or task with defined requirements or acceptance criteria, when the user asks for a "minimal", "scoped", or "surgical" change, or when a change must stay strictly within stated requirements. Also use when the user wants a template for writing a tightly scoped task prompt.
---

# Scoped Task Execution

## Operating principle

Deliver the smallest correct change that satisfies the stated acceptance criteria. Do not expand the task into cleanup, redesign, migration, refactoring, or adjacent fixes unless they are necessary for the requested outcome.

## 1. Intake

Before editing, extract four lists from the task:

1. Required behavior
2. Acceptance criteria
3. Explicit exclusions
4. Required verification

Treat explicit exclusions as hard constraints.

Do not look up Linear, other tickets, other branches, PRs, or external context unless the task explicitly requests it or the supplied task cannot be understood without it.

Ask one focused question only when the answer would materially change the implementation. Otherwise, inspect the code and state any minor assumption.

## 2. Establish ownership

Inspect the current worktree and relevant guidance files.

Search in this order:

1. Exact symbols and strings named in the task
2. Existing configuration or data source
3. Current UI or API consumer
4. Downstream behavior
5. Existing tests

Build a short ownership map:

```text
Source of truth
      │
      ├────▶ User-facing behavior
      ├────▶ Runtime behavior
      └────▶ Persistence / output
```

Do not edit until it is clear which module owns the behavior.

## 3. Choose the minimum change

Prefer, in order:

1. Updating an existing source-of-truth value
2. Extending an existing pattern
3. Editing an existing owner module
4. Adding a new abstraction only when the existing design cannot support the requirement

Before adding a file, helper, type, endpoint, flag, migration, or component, prove that the existing path cannot deliver the requirement.

Every production edit must map to:

- A stated acceptance criterion, or
- A necessary dependency of that criterion

If an edit maps to neither, leave it out.

## 4. Preserve existing paths

When the task says to reuse existing behavior, verify that behavior instead of rebuilding it.

Examples:

- If a shared catalog feeds Settings, add the item to the catalog.
- If enabled configuration already feeds prompts, do not add prompt-specific logic.
- If extraction is generic, do not add field-specific rendering.
- If absence already means disabled, do not add a migration to persist disabled rows.

Follow references far enough to confirm the contract, then stop.

## 5. Implement

Make the production change first.

Rules:

- Use exact names, descriptions, defaults, and types supplied by the task.
- Match existing ordering and formatting.
- Do not alter unrelated code.
- Do not modify unexpected worktree changes.
- Do not add comments that restate the code.
- Do not introduce speculative configurability.

## 6. Add focused coverage

Tests should prove the new requirement at existing boundaries.

Prefer:

1. A source-of-truth or configuration test
2. One integration test proving the existing downstream path receives the new value
3. Existing broad tests for regression coverage

Avoid duplicating every generic behavior for each new item.

Test explicit negative requirements when important:

- Disabled by default
- Excluded when absent
- Optional behavior does not block progress
- No extra node, API, or migration needed

## 7. Verify in increasing scope

Run checks in this order:

1. Formatter or formatting check on changed files
2. Focused tests
3. Typecheck
4. Required full test suite
5. Lint on changed files
6. Domain-specific generation or structural validation

Use repository-provided commands exactly.

Do not create external resources merely to validate local generation. For example, generate and inspect a local API payload instead of creating a live agent.

Delete temporary validation artifacts when finished.

## 8. Handle failures carefully

When a check fails:

1. Read the actual error.
2. Determine whether it is caused by the change.
3. Fix the cause.
4. Rerun the smallest relevant check.
5. Run the required broad check afterward.

Do not weaken tests, suppress failures, or hard-code test-only behavior.

If an external write reports an uncertain result, inspect the remote state before retrying.

## 9. External and Git actions

The implementation request does not implicitly authorize:

- Commits
- Pushes
- Branch deletion
- PR creation or editing
- Deployments
- Releases
- Database writes
- Creating third-party resources

Perform these only when explicitly requested.

When PR work is requested:

1. Read the repository's PR format.
2. Read the current PR.
3. Cover the whole branch.
4. Include only checks that actually passed.
5. Apply the update.
6. Re-read or inspect the response to verify it.

## 10. Final report

Keep the completion message short. Include:

- What changed
- Why the existing path was sufficient
- Verification results
- Any unresolved blocker

Do not provide a command transcript or narrate routine exploration.

## Copy-paste task template

Offer this template when the user wants to write a scoped task prompt:

```text
Implement this as a tightly scoped task.

Goal:
[Desired outcome]

Requirements:
- [Required behavior]
- [Required behavior]

Acceptance criteria:
- [Observable result]
- [Observable result]
- [Required checks]

Explicit exclusions:
- Do not add [migration/API/UI/flag/etc.]
- Do not refactor unrelated code.
- Do not inspect Linear, other tickets, or other branches unless explicitly required.
- Do not commit, push, deploy, or update a PR unless separately requested.

Execution rules:
1. Inspect the current implementation and identify the existing source of truth.
2. Reuse existing UI, runtime, persistence, and output paths where possible.
3. Make the smallest production diff that satisfies every acceptance criterion.
4. Every production edit must map to an acceptance criterion or a necessary dependency.
5. Ask one focused question only if ambiguity would materially change the outcome.
6. Add focused tests at the existing ownership boundaries.
7. Run the repository's required formatter, focused tests, typecheck, full tests, lint, and domain-specific validation.
8. Avoid external side effects during verification.
9. Report the change, verification results, and any blocker concisely.
```
