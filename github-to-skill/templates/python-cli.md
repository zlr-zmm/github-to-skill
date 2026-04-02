---
name: {{skill_name}}
description: {{trigger_description}}
github_url: {{github_url}}
github_hash: {{pinned_hash}}
version: {{version}}
created_at: {{created_date}}
entry_point: {{entry_point}}
dependencies:
  - python >= {{python_version}}
  - {{main_dependencies}}
status: {{status}}
---

# {{skill_name}}

## Scope

This skill provides CLI interface for {{repo_name}}.

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

```bash
# Clone repository
git clone {{github_url}} {{install_dir}}
cd {{install_dir}}

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
# or: pip install .
```

## Constraints

1. Requires Python {{python_version}}+
2. {{constraint_1}}
3. {{constraint_2}}

## Validation

Run these commands to verify installation:

```bash
# Basic smoke test
{{cli_name}} --help

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
import sys
from pathlib import Path

REPO_PATH = Path(__file__).parent.parent / "{{install_dir}}"

def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Execute {{cli_name}} with arguments."""
    cmd = [sys.executable, str(REPO_PATH / "{{entry_script}}"), *args]
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