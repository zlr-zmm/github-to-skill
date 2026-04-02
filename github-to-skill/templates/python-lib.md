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

This skill provides Python library interface for {{repo_name}}.

## Capabilities

### Capability: {{capability_name}}

{{#capabilities}}
#### {{name}}

**Description**: {{description}}

**Function Signature**:

```python
{{function_signature}}
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
{{#parameters}}
| {{name}} | {{type}} | {{required}} | {{default}} | {{description}} |
{{/parameters}}

**Returns**:

- `{{return_type}}`: {{return_description}}

**Example**:

```python
{{example_code}}
```

{{/capabilities}}

## Installation

```bash
# Install via pip (recommended)
pip install {{package_name}}

# Or install from source
git clone {{github_url}} {{install_dir}}
cd {{install_dir}}
pip install -e .
```

## Usage Pattern

```python
# Import the library
from {{module_name}} import {{main_class_or_function}}

# Initialize if needed
{{init_code}}

# Use capabilities
{{usage_example}}
```

## Constraints

1. Requires Python {{python_version}}+
2. {{constraint_1}}
3. {{constraint_2}}

## API Reference

### Core Classes/Functions

{{#api_reference}}
#### `{{name}}`

{{description}}

```python
{{signature}}
```

{{/api_reference}}

## Validation

```python
# Verify installation
try:
    from {{module_name}} import {{main_import}}
    print("Installation verified: {{module_name}}")
except ImportError as e:
    print(f"Installation failed: {e}")

# Functional test
{{functional_test_code}}
```

{{#if partial}}
> WARNING: Partial validation. The following capabilities are not locally verified:
> - {{unverified_capability}}: {{reason}}
> Unblock step: {{unblock_action}}
{{/if}}