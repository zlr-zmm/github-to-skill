---
name: <target-skill-name>
description: <trigger-oriented description>
github_url: <source-repo-url>
github_hash: <pinned-commit-hash>
version: <tag-or-0.1.0>
created_at: <YYYY-MM-DD>
entry_point: <main-command>
dependencies:
  - <dep1>
  - <dep2>
status: <ready|partial|blocked>
---

# <Target Skill Name>

## Scope

This skill covers only verified capabilities from `<repo-name>`.

## Capabilities

### Capability: <name>

Code check: ✓

Command:

```bash
<runnable-command>
```

Input:

- <required-input>

Output:

- <expected-output>

Evidence:

- <Wiki-or-README-reference>

## Constraints

- <runtime-limits>

## Validation

- command: `<runnable-command>`
- output check: `<path-or-response-check>`

> WARNING: Partial validation. The following capabilities are not locally verified:
> - [Capability]: [Reason]
> Unblock step: [Action]
