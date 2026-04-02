# Phase 3: Validate

## Goal

Confirm the generated skill is runnable and evidence-backed.

## Required Validation

1. Run at least one command from the capability matrix successfully.
2. Verify output existence (file or response evidence).
3. Complete a test report.

## Status Rules

1. `ready`: all required checks pass.
2. `partial`: some capabilities are not validated.
3. `blocked`: environment or core execution cannot proceed.

For `partial`, include the warning block in generated skill docs.

## Validation Examples

```powershell
<validated-command>
Test-Path <expected-output-path>
```

## Exit Criteria

Test report must include:

1. Environment
2. Commands executed
3. Status per case
4. Output proof (absolute path or response)
5. Unblock steps when not fully validated
