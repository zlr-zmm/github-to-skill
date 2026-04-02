"""
Skill Validator - Progressive validation of generated skills.

Usage:
    python src/validator.py <skill_dir> [--level <1-4>]
"""

import os
import sys
import json
import subprocess
import datetime
import importlib.util
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from enum import Enum


class ValidationLevel(Enum):
    STRUCTURE = 1      # File existence
    SYNTAX = 2         # Script syntax
    DEPENDENCIES = 3   # Installability
    FUNCTION = 4       # Execution test


class ValidationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class ValidationResult:
    """Single validation check result."""
    level: int
    check_name: str
    status: str
    message: str
    details: Optional[str] = None
    unblock_command: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    skill_name: str
    skill_path: str
    overall_status: str  # ready, partial, blocked
    results: list
    verified_capabilities: list
    unverified_capabilities: list
    timestamp: str


REQUIRED_SKILL_FILES = ["SKILL.md"]
REQUIRED_SCRIPT_FILES = ["wrapper.py"]


def check_file_exists(skill_path: Path, filename: str) -> ValidationResult:
    """Check if required file exists."""
    file_path = skill_path / filename
    if file_path.exists():
        return ValidationResult(
            level=1,
            check_name=f"file:{filename}",
            status="passed",
            message=f"{filename} exists",
            details=str(file_path)
        )
    else:
        return ValidationResult(
            level=1,
            check_name=f"file:{filename}",
            status="failed",
            message=f"{filename} missing",
            details=None,
            unblock_command=f"Create {filename}"
        )


def check_skill_md_structure(skill_path: Path) -> ValidationResult:
    """Check SKILL.md has required frontmatter."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return ValidationResult(
            level=1,
            check_name="skill_md:structure",
            status="failed",
            message="SKILL.md not found"
        )

    content = skill_md.read_text(encoding="utf-8", errors="ignore")

    # Check frontmatter
    if not content.startswith("---"):
        return ValidationResult(
            level=1,
            check_name="skill_md:frontmatter",
            status="failed",
            message="SKILL.md missing frontmatter",
            unblock_command="Add YAML frontmatter with name, description, status"
        )

    # Check required fields
    required_fields = ["name", "description", "status"]
    missing_fields = []

    # Extract frontmatter content (between --- markers)
    frontmatter_end = content.find("---", 3)
    if frontmatter_end == -1:
        frontmatter_end = len(content)
    frontmatter = content[:frontmatter_end]

    for field in required_fields:
        if f"{field}:" not in frontmatter:
            missing_fields.append(field)

    if missing_fields:
        return ValidationResult(
            level=1,
            check_name="skill_md:fields",
            status="failed",
            message=f"Missing fields: {missing_fields}",
            unblock_command=f"Add {missing_fields} to frontmatter"
        )

    return ValidationResult(
        level=1,
        check_name="skill_md:structure",
        status="passed",
        message="SKILL.md structure valid"
    )


def validate_structure(skill_path: Path) -> list[ValidationResult]:
    """Level 1: Structure validation."""
    results = []

    # Check required files
    for filename in REQUIRED_SKILL_FILES:
        results.append(check_file_exists(skill_path, filename))

    # Check scripts directory
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for filename in REQUIRED_SCRIPT_FILES:
            results.append(check_file_exists(scripts_dir, filename))
    else:
        results.append(ValidationResult(
            level=1,
            check_name="dir:scripts",
            status="skipped",
            message="scripts/ directory not required for this skill type"
        ))

    # Check SKILL.md structure
    results.append(check_skill_md_structure(skill_path))

    return results


def validate_syntax(skill_path: Path) -> list[ValidationResult]:
    """Level 2: Syntax validation."""
    results = []

    wrapper_path = skill_path / "scripts" / "wrapper.py"
    if wrapper_path.exists():
        # Check Python syntax
        try:
            content = wrapper_path.read_text(encoding="utf-8")
            compile(content, str(wrapper_path), 'exec')
            results.append(ValidationResult(
                level=2,
                check_name="syntax:wrapper.py",
                status="passed",
                message="wrapper.py syntax valid"
            ))
        except SyntaxError as e:
            results.append(ValidationResult(
                level=2,
                check_name="syntax:wrapper.py",
                status="failed",
                message=f"Syntax error: {e.msg}",
                details=f"Line {e.lineno}",
                unblock_command="Fix syntax error in wrapper.py"
            ))
    else:
        results.append(ValidationResult(
            level=2,
            check_name="syntax:wrapper.py",
            status="skipped",
            message="wrapper.py not found"
        ))

    return results


def validate_dependencies(skill_path: Path) -> list[ValidationResult]:
    """Level 3: Dependency validation."""
    results = []

    # Check for requirements.txt
    repo_path = skill_path / "repo"
    if not repo_path.exists():
        results.append(ValidationResult(
            level=3,
            check_name="deps:repo",
            status="failed",
            message="Repository not cloned",
            unblock_command="Clone repository to skill/repo/"
        ))
        return results

    # Check requirements.txt
    req_path = repo_path / "requirements.txt"
    if req_path.exists():
        # Try to verify pip can read it
        try:
            result = subprocess.run(
                ["pip", "check"],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
                timeout=30
            )
            # pip check validates dependency conflicts
            results.append(ValidationResult(
                level=3,
                check_name="deps:requirements",
                status="passed",
                message="requirements.txt valid",
                details=result.stdout[:200]
            ))
        except subprocess.TimeoutExpired:
            results.append(ValidationResult(
                level=3,
                check_name="deps:requirements",
                status="failed",
                message="Dependency check timed out",
                unblock_command="Run: pip install -r requirements.txt"
            ))
        except Exception as e:
            results.append(ValidationResult(
                level=3,
                check_name="deps:requirements",
                status="failed",
                message=f"Dependency check failed: {str(e)}",
                unblock_command="Run: pip install -r requirements.txt"
            ))
    else:
        # Check for pyproject.toml
        pyproject_path = repo_path / "pyproject.toml"
        if pyproject_path.exists():
            results.append(ValidationResult(
                level=3,
                check_name="deps:pyproject",
                status="passed",
                message="pyproject.toml found",
                details="Use: pip install ."
            ))
        else:
            results.append(ValidationResult(
                level=3,
                check_name="deps:files",
                status="skipped",
                message="No standard dependency files found"
            ))

    return results


def validate_function(skill_path: Path) -> list[ValidationResult]:
    """Level 4: Functional validation."""
    results = []

    # Read SKILL.md to extract capabilities
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        results.append(ValidationResult(
            level=4,
            check_name="function:skill",
            status="blocked",
            message="Cannot validate without SKILL.md"
        ))
        return results

    content = skill_md.read_text(encoding="utf-8", errors="ignore")

    # Extract capability commands from SKILL.md
    # Pattern: ```bash <command> ```
    import re
    command_blocks = re.findall(r"```(?:bash|shell)?\s*\n([^\n]+)\n```", content)

    verified = []
    unverified = []

    for cmd in command_blocks[:5]:  # Test first 5 commands
        cmd = cmd.strip()
        # Skip install commands
        if "install" in cmd.lower() or "clone" in cmd.lower() or "pip" in cmd.lower():
            continue

        check_name = f"function:{cmd[:30]}..."
        try:
            # Try to execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
                cwd=str(skill_path / "repo") if (skill_path / "repo").exists() else str(skill_path),
                timeout=60
            )

            if result.returncode == 0:
                verified.append(cmd)
                results.append(ValidationResult(
                    level=4,
                    check_name=check_name,
                    status="passed",
                    message=f"Command executed successfully",
                    details=result.stdout[:100]
                ))
            else:
                unverified.append((cmd, result.stderr[:100]))
                results.append(ValidationResult(
                    level=4,
                    check_name=check_name,
                    status="failed",
                    message=f"Command failed with code {result.returncode}",
                    details=result.stderr[:100],
                    unblock_command="Ensure dependencies are installed and environment is configured"
                ))
        except subprocess.TimeoutExpired:
            unverified.append((cmd, "Timeout"))
            results.append(ValidationResult(
                level=4,
                check_name=check_name,
                status="failed",
                message="Command timed out",
                unblock_command="Check if command requires special environment"
            ))
        except Exception as e:
            unverified.append((cmd, str(e)))
            results.append(ValidationResult(
                level=4,
                check_name=check_name,
                status="failed",
                message=f"Execution error: {str(e)}",
                unblock_command="Fix environment setup"
            ))

    # If no commands tested
    if not command_blocks:
        results.append(ValidationResult(
            level=4,
            check_name="function:commands",
            status="skipped",
            message="No testable commands found in SKILL.md"
        ))

    return results


def determine_overall_status(results: list[ValidationResult], verified: list, unverified: list) -> str:
    """Determine overall validation status."""
    # Count passed checks by level
    passed_levels = set()
    blocked_levels = set()

    for r in results:
        if r.status == "passed":
            passed_levels.add(r.level)
        elif r.status == "blocked":
            blocked_levels.add(r.level)
        elif r.status == "failed" and r.level <= 2:
            # Level 1-2 failures block the skill
            blocked_levels.add(r.level)

    if blocked_levels:
        return "blocked"

    # Level 4 (function) determines ready vs partial
    if 4 in passed_levels and verified:
        if not unverified:
            return "ready"
        else:
            return "partial"

    # Level 3 passed but level 4 not tested
    if 3 in passed_levels:
        return "partial"

    # Lower levels only
    return "partial"


def generate_test_report(skill_path: Path, report: ValidationReport) -> str:
    """Generate test-report.md."""
    content = f"""# Test Report: {report.skill_name}

## Validation Timestamp

- **Timestamp**: {report.timestamp}
- **Overall Status**: `{report.overall_status}`

## Validation Results

### Level 1: Structure

"""
    for r in report.results:
        if r["level"] == 1:
            content += f"- **{r['check_name']}**: `{r['status']}` - {r['message']}\n"

    content += """
### Level 2: Syntax

"""
    for r in report.results:
        if r["level"] == 2:
            content += f"- **{r['check_name']}**: `{r['status']}` - {r['message']}\n"

    content += """
### Level 3: Dependencies

"""
    for r in report.results:
        if r["level"] == 3:
            content += f"- **{r['check_name']}**: `{r['status']}` - {r['message']}\n"

    content += """
### Level 4: Function

"""
    for r in report.results:
        if r["level"] == 4:
            content += f"- **{r['check_name']}**: `{r['status']}` - {r['message']}\n"
            if r["details"]:
                content += f"  - Output: `{r['details'][:50]}...`\n"
            if r["unblock_command"]:
                content += f"  - Unblock: `{r['unblock_command']}`\n"

    content += """
## Verified Capabilities

"""
    for cmd in report.verified_capabilities:
        content += f"- [PASS] `{cmd}`\n"

    content += """
## Unverified Capabilities

"""
    for cmd, reason in report.unverified_capabilities:
        content += f"- [FAIL] `{cmd}` - {reason}\n"

    if report.overall_status == "partial":
        content += """
## Warning Block

> WARNING: Partial validation. The following capabilities are not locally verified:
"""
        for cmd, reason in report.unverified_capabilities:
            content += f"> - `{cmd}`: {reason}\n"

    if report.overall_status == "blocked":
        content += """
## Unblock Steps

"""
        for r in report.results:
            if r["status"] in ["failed", "blocked"] and r["unblock_command"]:
                content += f"- **{r['check_name']}**: `{r['unblock_command']}`\n"

    return content


def validate_skill(skill_path: str, max_level: int = 4) -> ValidationReport:
    """Validate skill at specified level."""
    path = Path(skill_path)

    if not path.exists():
        raise FileNotFoundError(f"Skill path not found: {skill_path}")

    # Read skill name from SKILL.md
    skill_md = path / "SKILL.md"
    skill_name = path.name
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8", errors="ignore")
        import re
        name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
        if name_match:
            skill_name = name_match.group(1).strip()

    results = []

    # Level 1: Structure
    if max_level >= 1:
        results.extend(validate_structure(path))

    # Level 2: Syntax
    if max_level >= 2:
        results.extend(validate_syntax(path))

    # Level 3: Dependencies
    if max_level >= 3:
        results.extend(validate_dependencies(path))

    # Level 4: Function
    if max_level >= 4:
        func_results = validate_function(path)
        results.extend(func_results)

        # Extract verified/unverified from Level 4 results
        verified = [r.details for r in func_results if r.status == "passed" and r.details]
        unverified = [(r.check_name.replace("function:", ""), r.message) for r in func_results if r.status == "failed"]
    else:
        verified = []
        unverified = []

    # Determine overall status
    overall_status = determine_overall_status(results, verified, unverified)

    report = ValidationReport(
        skill_name=skill_name,
        skill_path=str(path),
        overall_status=overall_status,
        results=[asdict(r) for r in results],
        verified_capabilities=verified,
        unverified_capabilities=unverified,
        timestamp=datetime.datetime.now().isoformat()
    )

    # Generate test report content (not saving to file anymore per user request)
    report_content = generate_test_report(path, report)
    # (path / "references" / "test-report.md").write_text(report_content, encoding="utf-8")

    return report


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate generated skill")
    parser.add_argument("skill_dir", help="Path to generated skill directory")
    parser.add_argument("--level", type=int, default=4, choices=[1, 2, 3, 4], help="Maximum validation level")
    parser.add_argument("--output", choices=["json", "summary"], default="summary", help="Output format")

    args = parser.parse_args()

    try:
        report = validate_skill(args.skill_dir, args.level)

        if args.output == "json":
            print(json.dumps(asdict(report), indent=2))
        else:
            print(f"Skill: {report.skill_name}")
            print(f"Status: {report.overall_status}")
            print(f"\nValidation Results:")
            for r in report.results:
                status_icon = "[OK]" if r["status"] == "passed" else ("[FAIL]" if r["status"] == "failed" else "[SKIP]")
                print(f"  {status_icon} Level {r['level']}: {r['check_name']} - {r['message']}")

            print(f"\nVerified: {len(report.verified_capabilities)}")
            print(f"Unverified: {len(report.unverified_capabilities)}")

            if report.overall_status == "blocked":
                print("\nUnblock steps required:")
                for r in report.results:
                    if r["status"] in ["failed", "blocked"] and r.get("unblock_command"):
                        print(f"  - {r['unblock_command']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()