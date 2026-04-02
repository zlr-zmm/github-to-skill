---
name: {{skill_name}}
description: {{trigger_description}}
github_url: {{github_url}}
github_hash: {{pinned_hash}}
version: {{version}}
created_at: {{created_date}}
entry_point: {{entry_point}}
dependencies:
  - rust >= {{rust_version}}
  - cargo >= {{cargo_version}}
status: {{status}}
---

# {{skill_name}}

## Scope

This skill provides CLI interface for {{repo_name}} (Rust).

## Capabilities

### Capability: {{capability_name}}

{{#capabilities}}
#### {{name}}

**Description**: {{description}}

**Command**:

```bash
{{command}}
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
{{#parameters}}
| {{name}} | {{type}} | {{required}} | {{default}} | {{description}} |
{{/parameters}}

**Input**:

- {{input_description}}

**Output**:

- {{output_description}}

**Example**:

```bash
{{example_command}}
```

{{/capabilities}}

## Installation

### Option 1: Pre-built Binary (Recommended)

```bash
# Download from releases
# https://github.com/{{repo_owner}}/{{repo_name}}/releases

# Or use cargo-binstall
cargo binstall {{crate_name}}
```

### Option 2: Build from Source

```bash
# Clone repository
git clone {{github_url}} {{install_dir}}
cd {{install_dir}}

# Build
cargo build --release

# Binary location
./target/release/{{binary_name}}
```

## Constraints

1. Requires Rust {{rust_version}}+ for building from source
2. {{constraint_1}}
3. {{constraint_2}}

## Validation

```bash
# Basic smoke test
{{binary_name}} --help

# Functional test
{{functional_test_command}}
```

Expected outputs:

1. `--help` shows usage information
2. Functional test returns expected result

## Wrapper Script

```python
# scripts/wrapper.py
import subprocess
from pathlib import Path

# Use pre-built binary or built binary
BINARY_PATH = Path(__file__).parent.parent / "{{install_dir}}/target/release/{{binary_name}}"
# Alternative: system binary
# BINARY_PATH = "{{binary_name}}"  # if installed globally

def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Execute {{binary_name}} with arguments."""
    cmd = [str(BINARY_PATH), *args]
    return subprocess.run(cmd, capture_output=True, text=True)

def {{capability_function}}({{params}}) -> str:
    """{{capability_description}}."""
    result = run_cli(["{{cli_args}}"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout
```

{{#if partial}}
> WARNING: Partial validation. The following capabilities are not locally verified:
> - {{unverified_capability}}: {{reason}}
> Unblock step: {{unblock_action}}
{{/if}}