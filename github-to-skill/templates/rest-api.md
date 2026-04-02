---
name: {{skill_name}}
description: {{trigger_description}}
github_url: {{github_url}}
github_hash: {{pinned_hash}}
version: {{version}}
created_at: {{created_date}}
entry_point: {{api_base_url}}
dependencies:
  - {{server_requirements}}
  - {{client_requirements}}
status: {{status}}
---

# {{skill_name}}

## Scope

This skill provides API interface for {{repo_name}} REST API.

## Capabilities

### Capability: {{capability_name}}

{{#capabilities}}
#### {{name}}

**Description**: {{description}}

**HTTP Method**: `{{method}}`

**Endpoint**: `{{endpoint}}`

**Request Parameters**:

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
{{#parameters}}
| {{name}} | {{type}} | {{location}} | {{required}} | {{description}} |
{{/parameters}}

**Request Body**:

```json
{{request_body_example}}
```

**Response**:

```json
{{response_example}}
```

**Example**:

```bash
curl -X {{method}} "{{api_base_url}}{{endpoint}}" \
  -H "Content-Type: application/json" \
  -d '{{request_body}}'
```

{{/capabilities}}

## Server Setup

```bash
# Clone repository
git clone {{github_url}} {{install_dir}}
cd {{install_dir}}

# Install dependencies
{{install_command}}

# Start server
{{start_command}}

# Server will run at {{api_base_url}}
```

## Client Usage

```python
# scripts/client.py
import requests
from typing import Optional, dict, Any

API_BASE = "{{api_base_url}}"

def {{capability_function}}({{params}}) -> dict[str, Any]:
    """{{capability_description}}."""
    response = requests.{{method}}(
        f"{API_BASE}{{endpoint}}",
        {{request_params}}
    )
    response.raise_for_status()
    return response.json()
```

## Constraints

1. Requires running server at {{api_base_url}}
2. {{constraint_1}}
3. {{constraint_2}}

## Authentication

{{#if auth_required}}
| Type | Parameter | Location | Description |
|------|-----------|----------|-------------|
| {{auth_type}} | {{auth_param}} | {{auth_location}} | {{auth_description}} |
{{/if}}

## Validation

```bash
# Check server health
curl "{{api_base_url}}/health"

# Test API endpoint
{{test_command}}
```

Expected outputs:

1. Health check returns `{"status": "ok"}` or similar
2. Test endpoint returns expected response

{{#if partial}}
> WARNING: Partial validation. The following capabilities are not locally verified:
> - {{unverified_capability}}: {{reason}}
> Unblock step: {{unblock_action}}
{{/if}}