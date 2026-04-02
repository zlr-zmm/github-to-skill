"""
Skill Generator - Generate SKILL.md from project profile using templates.

Usage:
    python src/generator.py <profile_json> [--template <type>] [--output <dir>]
"""

import os
import sys
import json
import datetime
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Any

# Import detector module
try:
    from detector import ProjectProfile, ProjectType, BuildSystem, EntryPoint
except ImportError:
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from detector import ProjectProfile, ProjectType, BuildSystem, EntryPoint


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class CapabilitySpec:
    """Extracted capability specification."""
    name: str
    description: str
    command: str
    parameters: list
    input_description: str
    output_description: str
    example_command: str
    evidence_source: str
    code_checked: bool


@dataclass
class GeneratedSkill:
    """Generated skill structure."""
    name: str
    path: str
    skill_md: str
    wrapper_script: str
    source_notes: str
    workflow: str
    status: str
    created_at: str


def load_template(template_type: str) -> str:
    """Load template by type."""
    template_map = {
        ProjectType.PYTHON_CLI: "python-cli.md",
        ProjectType.PYTHON_LIB: "python-lib.md",
        ProjectType.NODE_CLI: "node-cli.md",
        ProjectType.NODE_LIB: "node-cli.md",  # Similar structure
        ProjectType.RUST_CLI: "rust-cli.md",
        ProjectType.RUST_LIB: "rust-cli.md",
        ProjectType.GO_CLI: "rust-cli.md",  # Similar binary structure
        ProjectType.GO_LIB: "rust-cli.md",
        ProjectType.REST_API: "rest-api.md",
    }

    template_file = template_map.get(template_type, "python-cli.md")
    template_path = TEMPLATES_DIR / template_file

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def generate_safe_skill_name(repo_name: str) -> str:
    """Generate safe skill name from repository name."""
    # Remove special characters, lowercase, replace with hyphens
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in repo_name)
    safe = safe.lower().strip("-")
    # Remove consecutive hyphens
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe


def extract_capabilities_from_readme(readme_path: Optional[Path], project_type: ProjectType) -> list[CapabilitySpec]:
    """Extract capabilities from README content."""
    capabilities = []

    if not readme_path or not readme_path.exists():
        return capabilities

    readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")

    # Look for common patterns in README
    # Pattern 1: Code blocks with commands
    code_blocks = re.findall(r"```(?:bash|shell|sh)?\s*\n([^`]+)\n```", readme_content, re.IGNORECASE)

    for i, block in enumerate(code_blocks[:5]):  # Limit to first 5
        block = block.strip()
        # Skip obvious non-executable blocks
        if block.startswith("#") or "install" in block.lower()[:20]:
            continue

        capabilities.append(CapabilitySpec(
            name=f"Command Example {i+1}",
            description=f"Extracted from README code block",
            command=block,
            parameters=[],
            input_description="As documented in README",
            output_description="As documented in README",
            example_command=block,
            evidence_source="README",
            code_checked=False
        ))

    return capabilities


def extract_capabilities_from_entry_points(entry_points: list[EntryPoint], project_type: ProjectType) -> list[CapabilitySpec]:
    """Generate capabilities from detected entry points."""
    capabilities = []

    for ep in entry_points[:5]:  # Limit to first 5
        if ep.type == "cli":
            # CLI entry point
            cmd = ep.name if project_type in [ProjectType.PYTHON_CLI, ProjectType.NODE_CLI] else ep.name
            capabilities.append(CapabilitySpec(
                name=f"{ep.name} CLI",
                description=f"CLI command: {ep.name}",
                command=f"{cmd} --help",
                parameters=[
                    {"name": "args", "type": "string", "required": False, "description": "Command arguments"}
                ],
                input_description="Command-line arguments",
                output_description="Command output (stdout)",
                example_command=f"{cmd} --version",
                evidence_source="Entry point detection",
                code_checked=True
            ))
        elif ep.type == "module":
            # Library entry point
            capabilities.append(CapabilitySpec(
                name=f"Import {ep.name}",
                description=f"Python module: {ep.path}",
                command=f"from {ep.path.replace('/', '.').replace('.py', '')} import *",
                parameters=[],
                input_description="Python import",
                output_description="Module objects",
                example_command=f"import {ep.path.replace('/', '.').replace('.py', '')}",
                evidence_source="Entry point detection",
                code_checked=True
            ))

    return capabilities


def generate_wrapper_script(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate wrapper script based on project type."""
    if profile.project_type in [ProjectType.PYTHON_CLI, ProjectType.PYTHON_LIB]:
        return generate_python_wrapper(profile, capabilities)
    elif profile.project_type in [ProjectType.NODE_CLI, ProjectType.NODE_LIB]:
        return generate_node_wrapper(profile, capabilities)
    elif profile.project_type in [ProjectType.RUST_CLI, ProjectType.RUST_LIB, ProjectType.GO_CLI, ProjectType.GO_LIB]:
        return generate_binary_wrapper(profile, capabilities)
    elif profile.project_type == ProjectType.REST_API:
        return generate_api_wrapper(profile, capabilities)
    else:
        return generate_generic_wrapper(profile, capabilities)


def generate_python_wrapper(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate Python wrapper script."""
    skill_name = generate_safe_skill_name(profile.name)

    wrapper = f'''"""
Wrapper script for {profile.name} skill.

This script provides a Python interface to execute {profile.name} capabilities.
"""
import subprocess
import sys
from pathlib import Path

# Repository path (adjust after installation)
REPO_PATH = Path(__file__).parent.parent / "repo"

def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Execute CLI command with arguments."""
    # Determine entry point
    entry_script = REPO_PATH / "{profile.entry_points[0].path if profile.entry_points else 'main.py'}"
    cmd = [sys.executable, str(entry_script), *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_PATH))

'''

    # Add capability functions
    for cap in capabilities[:5]:
        func_name = cap.name.lower().replace("-", "_").replace(" ", "_")
        wrapper += f'''
def {func_name}(*args) -> str:
    """{cap.description}"""
    result = run_cli(list(args))
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {{result.stderr}}")
    return result.stdout

'''

    return wrapper


def generate_node_wrapper(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate Node.js wrapper script."""
    skill_name = generate_safe_skill_name(profile.name)

    wrapper = f'''"""
Wrapper script for {profile.name} skill (Node.js).

This script provides a Python interface to execute Node CLI.
"""
import subprocess
import sys
from pathlib import Path

REPO_PATH = Path(__file__).parent.parent / "repo"

def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Execute Node CLI with arguments."""
    cmd = ["npx", "{profile.entry_points[0].name if profile.entry_points else profile.name}", *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_PATH))

'''

    for cap in capabilities[:5]:
        func_name = cap.name.lower().replace("-", "_").replace(" ", "_")
        wrapper += f'''
def {func_name}(*args) -> str:
    """{cap.description}"""
    result = run_cli(list(args))
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {{result.stderr}}")
    return result.stdout

'''

    return wrapper


def generate_binary_wrapper(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate binary wrapper for Rust/Go projects."""
    skill_name = generate_safe_skill_name(profile.name)
    binary_name = profile.entry_points[0].name if profile.entry_points else profile.name

    wrapper = f'''"""
Wrapper script for {profile.name} skill (Binary).

This script provides a Python interface to execute compiled binary.
"""
import subprocess
import sys
from pathlib import Path

# Binary path (adjust after installation)
BINARY_PATH = Path(__file__).parent.parent / "repo" / "target" / "release" / "{binary_name}"

def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Execute binary with arguments."""
    cmd = [str(BINARY_PATH), *args]
    return subprocess.run(cmd, capture_output=True, text=True)

'''

    for cap in capabilities[:5]:
        func_name = cap.name.lower().replace("-", "_").replace(" ", "_")
        wrapper += f'''
def {func_name}(*args) -> str:
    """{cap.description}"""
    result = run_cli(list(args))
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {{result.stderr}}")
    return result.stdout

'''

    return wrapper


def generate_api_wrapper(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate REST API wrapper."""
    wrapper = '''"""
Wrapper script for REST API skill.

This script provides a Python interface to call REST API endpoints.
"""
import requests
from typing import Any

API_BASE = "http://localhost:8000"  # Adjust after server setup

def call_api(method: str, endpoint: str, **kwargs) -> dict[str, Any]:
    """Call API endpoint."""
    response = requests.request(method, f"{API_BASE}{endpoint}", **kwargs)
    response.raise_for_status()
    return response.json()

'''

    for cap in capabilities[:5]:
        func_name = cap.name.lower().replace("-", "_").replace(" ", "_")
        wrapper += f'''
def {func_name}() -> dict:
    """{cap.description}"""
    return call_api("GET", "/{func_name}")

'''

    return wrapper


def generate_generic_wrapper(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate generic wrapper for unknown project types."""
    return f'''"""
Generic wrapper script for {profile.name} skill.

Manual customization required based on project type.
"""
# TODO: Customize this wrapper based on actual project structure
print("Wrapper script placeholder for {profile.name}")
'''


def render_skill_md(profile: ProjectProfile, capabilities: list[CapabilitySpec], template: str) -> str:
    """Render SKILL.md from template and profile."""
    skill_name = generate_safe_skill_name(profile.name)
    created_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Simple template substitution (can be enhanced with Jinja2)
    # Use placeholder format: {{variable}}

    # Build capabilities markdown
    caps_md = ""
    for cap in capabilities[:10]:
        params_table = "| Parameter | Type | Required | Description |\n|-----------|------|----------|-------------|\n"
        for p in cap.parameters:
            params_table += f"| {p.get('name', '')} | {p.get('type', '')} | {p.get('required', 'no')} | {p.get('description', '')} |\n"
        if not cap.parameters:
            params_table = "None\n"

        caps_md += f"""
### Capability: {cap.name}

**Description**: {cap.description}

**Command**:

```bash
{cap.command}
```

**Parameters**:

{params_table}

**Input**: {cap.input_description}

**Output**: {cap.output_description}

**Example**:

```bash
{cap.example_command}
```

**Evidence**: {cap.evidence_source}

"""
    # Determine status
    verified_count = sum(1 for c in capabilities if c.code_checked)
    status = "ready" if verified_count >= 1 else "partial"
    if not profile.entry_points:
        status = "blocked"

    # Build final skill.md
    skill_md = f"""---
name: {skill_name}
description: Skill wrapper for {profile.name}. Auto-generated from GitHub repository.
github_url: Unknown
github_hash: Unknown
version: 0.1.0
created_at: {created_date}
entry_point: {profile.entry_points[0].name if profile.entry_points else 'unknown'}
dependencies:
  - {profile.language}
status: {status}
---

# {skill_name}

## Scope

This skill wraps capabilities from **{profile.name}**.

**Project Type**: {profile.project_type.value}

**Language**: {profile.language}

**Build System**: {profile.build_system.value}

## First Time Used

Before using this skill for the first time, you must clone the target repository and set up its environment locally within the skill folder:

```bash
# Clone repository
git clone <github_url> repo
cd repo

# Install dependencies
"""
    if profile.project_type in [ProjectType.PYTHON_CLI, ProjectType.PYTHON_LIB]:
        skill_md += """python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
"""
    elif profile.project_type in [ProjectType.NODE_CLI, ProjectType.NODE_LIB]:
        skill_md += """npm install
"""
    elif profile.project_type in [ProjectType.RUST_CLI, ProjectType.RUST_LIB]:
        skill_md += """cargo build --release
"""

    skill_md += f"""
```

## Capabilities

{caps_md}

## Constraints

1. Requires {profile.language} runtime
2. {f"Entry point: {profile.entry_points[0].path}" if profile.entry_points else "No entry points detected"}
3. Confidence score: {profile.confidence:.2f}

## Validation

```bash
# Basic test
"""
    if profile.entry_points:
        skill_md += f"{profile.entry_points[0].name} --help\n"

    skill_md += """
```

"""
    if status == "partial":
        skill_md += f"""
> WARNING: Partial validation. The following capabilities are not locally verified:
> - Capabilities extracted from README require runtime verification
> Unblock step: Run skill locally and verify each capability
"""

    return skill_md


def generate_source_notes(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate source-notes.md."""
    notes = f"""# Source Notes: {profile.name}

## Repository Profile

- **Name**: {profile.name}
- **Type**: {profile.project_type.value}
- **Language**: {profile.language}
- **Build System**: {profile.build_system.value}
- **Confidence**: {profile.confidence:.2f}

## Detection Timestamp

- **Collected at**: {datetime.datetime.now().isoformat()}

## Entry Points

"""
    for ep in profile.entry_points:
        notes += f"- **{ep.name}** ({ep.type}): `{ep.path}`\n"

    if not profile.entry_points:
        notes += "- No entry points detected\n"

    notes += """
## Dependencies

"""
    for dep in profile.dependencies:
        notes += f"- `{dep.file}`: {dep.count} dependencies, format: {dep.format}\n"
        if dep.main_deps:
            notes += f"  - Main: {', '.join(dep.main_deps[:5])}\n"

    notes += """
## Evidence Sources

"""
    for cap in capabilities:
        notes += f"- **{cap.name}**: {cap.evidence_source} (code-checked: {cap.code_checked})\n"

    notes += """
## Special Features

- **Tests**: {profile.has_tests}
- **Examples**: {profile.has_examples}
- **Docs**: {profile.has_docs}
- **README**: {profile.readme_path or 'Not found'}
- **License**: {profile.license or 'Unknown'}
"""

    return notes


def generate_workflow(profile: ProjectProfile, capabilities: list[CapabilitySpec]) -> str:
    """Generate workflow.md."""
    workflow = f"""# Workflow: {profile.name}

## Execution Flow

```mermaid
graph TD
    A[User Request] --> B[Skill Detection]
    B --> C[Capability Selection]
    C --> D[Wrapper Execution]
    D --> E[Output Return]
```

## Capability Map

"""
    for cap in capabilities[:10]:
        workflow += f"""
### {cap.name}

**Flow**:
1. User requests: `{cap.description}`
2. Wrapper executes: `{cap.command}`
3. Output: `{cap.output_description}`

"""

    return workflow


def generate_skill(profile: ProjectProfile, output_dir: Path, readme_path: Optional[Path] = None) -> GeneratedSkill:
    """Generate complete skill from project profile."""
    skill_name = generate_safe_skill_name(profile.name)
    skill_path = output_dir / skill_name

    # Create directory structure
    skill_path.mkdir(parents=True, exist_ok=True)
    (skill_path / "scripts").mkdir(exist_ok=True)
    (skill_path / "references").mkdir(exist_ok=True)

    # Extract capabilities
    readme_caps = extract_capabilities_from_readme(readme_path, profile.project_type)
    entry_caps = extract_capabilities_from_entry_points(profile.entry_points, profile.project_type)

    # Merge capabilities, prioritize code-checked ones
    capabilities = entry_caps + readme_caps

    if not capabilities:
        # Add placeholder capability
        capabilities.append(CapabilitySpec(
            name="Basic Execution",
            description="Placeholder - requires manual capability extraction",
            command=f"{profile.name} --help",
            parameters=[],
            input_description="Command arguments",
            output_description="Command output",
            example_command=f"{profile.name} --version",
            evidence_source="Placeholder",
            code_checked=False
        ))

    # Generate artifacts
    skill_md = render_skill_md(profile, capabilities, "")
    wrapper_script = generate_wrapper_script(profile, capabilities)
    source_notes = generate_source_notes(profile, capabilities)
    workflow = generate_workflow(profile, capabilities)

    # Write files
    (skill_path / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (skill_path / "scripts" / "wrapper.py").write_text(wrapper_script, encoding="utf-8")
    (skill_path / "references" / "source-notes.md").write_text(source_notes, encoding="utf-8")
    (skill_path / "references" / "workflow.md").write_text(workflow, encoding="utf-8")

    # Determine status
    verified_count = sum(1 for c in capabilities if c.code_checked)
    status = "ready" if verified_count >= 1 else "partial"
    if not profile.entry_points:
        status = "blocked"

    return GeneratedSkill(
        name=skill_name,
        path=str(skill_path),
        skill_md=skill_md,
        wrapper_script=wrapper_script,
        source_notes=source_notes,
        workflow=workflow,
        status=status,
        created_at=datetime.datetime.now().isoformat()
    )


def main():
    """CLI entry point."""
    import argparse
    import re  # Add re import for capability extraction

    parser = argparse.ArgumentParser(description="Generate skill from project profile")
    parser.add_argument("profile_json", help="Path to profile JSON from detector")
    parser.add_argument("--template", choices=["python-cli", "python-lib", "node-cli", "rust-cli", "rest-api"], help="Override template type")
    parser.add_argument("--output", default="generated", help="Output directory")
    parser.add_argument("--readme", help="Path to README file (optional)")

    args = parser.parse_args()

    # Load profile
    profile_path = Path(args.profile_json)
    if not profile_path.exists():
        print(f"Error: Profile not found: {profile_path}", file=sys.stderr)
        sys.exit(1)

    profile_data = json.loads(profile_path.read_text(encoding="utf-8"))

    # Convert to ProjectProfile
    profile = ProjectProfile(
        path=profile_data["path"],
        name=profile_data["name"],
        project_type=ProjectType(profile_data["project_type"]),
        build_system=BuildSystem(profile_data["build_system"]),
        language=profile_data["language"],
        entry_points=[EntryPoint(**ep) for ep in profile_data.get("entry_points", [])],
        dependencies=[],  # Simplified for this conversion
        has_tests=profile_data.get("has_tests", False),
        has_examples=profile_data.get("has_examples", False),
        has_docs=profile_data.get("has_docs", False),
        readme_path=profile_data.get("readme_path"),
        wiki_available=profile_data.get("wiki_available", False),
        license=profile_data.get("license"),
        confidence=profile_data.get("confidence", 0.0)
    )

    # Read README if provided
    readme_path = Path(args.readme) if args.readme else None
    if not readme_path and profile.readme_path:
        readme_path = Path(profile.path) / profile.readme_path

    # Generate skill
    output_dir = Path(args.output)
    skill = generate_skill(profile, output_dir, readme_path)

    # Print result
    print(json.dumps(asdict(skill), indent=2))
    print(f"\nSkill generated at: {skill.path}")
    print(f"Status: {skill.status}")
    print("\nNext steps:")
    print("1. Review generated SKILL.md")
    print("2. Run validator to verify installation")
    print("3. Test capabilities manually if needed")


if __name__ == "__main__":
    main()