# Test Report Template

Date: <YYYY-MM-DD>

## Environment

- OS: <os>
- Shell: <shell>
- Runtime: <python/node/etc>

## Validation Cases

### Case 1

- capability: <name>
- command: `<command>`
- status: <success|failed>
- output_proof: <absolute-path-or-response-proof>

### Case 2 (optional)

- capability: <name>
- command: `<command>`
- status: <success|failed>
- output_proof: <absolute-path-or-response-proof>

## Final Status

- status: <ready|partial|blocked>

If `partial`:

> WARNING: Partial validation. The following capabilities are not locally verified:
> - [Capability]: [Reason]
> Unblock step: [Action]

If `blocked`:

- blocker: <reason>
- unblock_command: `<next-command>`
