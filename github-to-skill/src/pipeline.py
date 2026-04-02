"""
GitHub to Skill Pipeline - Complete conversion pipeline.

Usage:
    python src/pipeline.py <github_url> [--output <dir>] [--auto]
    python src/pipeline.py <github_url> --interactive
"""

import os
import sys
import json
import subprocess
import argparse
import datetime
import shutil
import tempfile
from pathlib import Path
from dataclasses import asdict
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from detector import profile_project, ProjectProfile, ProjectType
    from generator import generate_skill, GeneratedSkill
    from validator import validate_skill, ValidationReport, ValidationStatus
except ImportError as e:
    print(f"Error loading modules: {e}", file=sys.stderr)
    sys.exit(1)


PIPELINE_STEPS = [
    ("detect", "Project profiling"),
    ("extract", "Evidence extraction"),
    ("generate", "Skill generation"),
    ("validate", "Progressive validation"),
    ("review", "User confirmation"),
]


def clone_repository(github_url: str, target_dir: Path) -> Path:
    """Clone GitHub repository to target directory."""
    # Extract repo name from URL
    repo_name = github_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    clone_path = target_dir / repo_name

    if clone_path.exists():
        print(f"Repository already cloned at: {clone_path}")
        return clone_path

    print(f"Cloning {github_url}...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", github_url, str(clone_path)],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode != 0:
        raise RuntimeError(f"Clone failed: {result.stderr}")

    return clone_path


def get_github_hash(repo_path: Path) -> str:
    """Get current commit hash from cloned repository."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(repo_path)
    )

    if result.returncode != 0:
        return "unknown"

    return result.stdout.strip()[:12]


def run_pipeline_step(step_name: str, step_func, *args, **kwargs) -> tuple[bool, Any]:
    """Run a pipeline step and return success status."""
    print(f"\n[Step: {step_name}]")
    try:
        result = step_func(*args, **kwargs)
        print(f"  ✓ {step_name} completed")
        return True, result
    except Exception as e:
        print(f"  ✗ {step_name} failed: {e}")
        return False, str(e)


def step_detect(repo_path: Path) -> ProjectProfile:
    """Step 1: Detect project profile."""
    profile = profile_project(str(repo_path))
    print(f"  Type: {profile.project_type.value}")
    print(f"  Language: {profile.language}")
    print(f"  Build: {profile.build_system.value}")
    print(f"  Confidence: {profile.confidence:.2f}")
    print(f"  Entry points: {len(profile.entry_points)}")
    return profile


def step_extract(repo_path: Path, profile: ProjectProfile) -> Path:
    """Step 2: Extract evidence (currently uses README)."""
    readme_path = None
    if profile.readme_path:
        readme_path = repo_path / profile.readme_path
        print(f"  README: {profile.readme_path}")
    else:
        # Try common readme names
        for name in ["README.md", "README.rst", "readme.md"]:
            path = repo_path / name
            if path.exists():
                readme_path = path
                print(f"  README: {name}")
                break

    if not readme_path:
        print("  WARNING: No README found")

    return readme_path


def step_generate(profile: ProjectProfile, readme_path: Optional[Path], output_dir: Path) -> GeneratedSkill:
    """Step 3: Generate skill artifacts."""
    skill = generate_skill(profile, output_dir, readme_path)
    print(f"  Skill name: {skill.name}")
    print(f"  Output path: {skill.path}")
    print(f"  Status: {skill.status}")
    return skill


def step_validate(skill_path: Path, level: int = 4) -> ValidationReport:
    """Step 4: Validate generated skill."""
    report = validate_skill(str(skill_path), level)
    print(f"  Overall: {report.overall_status}")
    print(f"  Verified: {len(report.verified_capabilities)}")
    print(f"  Unverified: {len(report.unverified_capabilities)}")
    return report


def step_review(skill: GeneratedSkill, report: ValidationReport, auto: bool = False) -> bool:
    """Step 5: User confirmation (interactive or auto)."""
    if auto:
        print("  Auto-approval: enabled")
        return report.overall_status in ["ready", "partial"]

    # Interactive review
    print("\n" + "=" * 50)
    print("GENERATED SKILL REVIEW")
    print("=" * 50)
    print(f"Skill: {skill.name}")
    print(f"Status: {report.overall_status}")
    print(f"Path: {skill.path}")
    print("\nGenerated files:")
    print("  - SKILL.md")
    print("  - scripts/wrapper.py")
    print("  - references/source-notes.md")
    print("  - references/workflow.md")

    if report.overall_status == "blocked":
        print("\nWARNING: Skill is blocked. Unblock steps required:")
        for r in report.results:
            if r["status"] in ["failed", "blocked"] and r.get("unblock_command"):
                print(f"  - {r['unblock_command']}")

    print("\nOptions:")
    print("  [a] Approve and continue")
    print("  [e] Edit SKILL.md manually")
    print("  [r] Reject and regenerate")
    print("  [q] Quit without saving")

    choice = input("\nChoice: ").strip().lower()

    if choice == "a":
        return True
    elif choice == "e":
        print(f"\nEdit: {skill.path}/SKILL.md")
        print("Press Enter after editing...")
        input()
        return True
    elif choice == "r":
        return False  # Will trigger regeneration
    else:
        return False


def run_full_pipeline(
    github_url: str,
    output_dir: Path,
    auto: bool = False,
    validation_level: int = 4,
    keep_repo: bool = False
) -> Optional[Path]:
    """Run complete pipeline from GitHub URL to generated skill."""

    print("=" * 50)
    print("GITHUB TO SKILL PIPELINE")
    print("=" * 50)
    print(f"URL: {github_url}")
    print(f"Output: {output_dir}")

    # Create temporary directory for cloning
    temp_dir = Path(tempfile.mkdtemp(prefix="github-skill-"))

    try:
        # Clone repository
        repo_path = clone_repository(github_url, temp_dir)
        github_hash = get_github_hash(repo_path)

        # Step 1: Detect
        success, profile = run_pipeline_step("detect", step_detect, repo_path)
        if not success:
            print("\nPipeline blocked at detection step")
            return None

        # Step 2: Extract
        success, readme_path = run_pipeline_step("extract", step_extract, repo_path, profile)

        # Step 3: Generate
        success, skill = run_pipeline_step(
            "generate",
            step_generate,
            profile,
            readme_path,
            output_dir
        )
        if not success:
            print("\nPipeline blocked at generation step")
            return None

        # Move repo to skill directory
        skill_repo_path = Path(skill.path) / "repo"
        if keep_repo:
            shutil.move(str(repo_path), str(skill_repo_path))
            print(f"\nRepository moved to: {skill_repo_path}")

        # Update SKILL.md with github info
        skill_md_path = Path(skill.path) / "SKILL.md"
        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            content = content.replace("github_url: Unknown", f"github_url: {github_url}")
            content = content.replace("github_hash: Unknown", f"github_hash: {github_hash}")
            content = content.replace("<github_url>", github_url)
            skill_md_path.write_text(content, encoding="utf-8")

        # Step 4: Validate
        success, report = run_pipeline_step(
            "validate",
            step_validate,
            Path(skill.path),
            validation_level
        )

        # Step 5: Review
        approved = step_review(skill, report, auto)

        if approved:
            print(f"\n✓ Skill generated successfully: {skill.path}")
            print(f"  Status: {report.overall_status}")
            return Path(skill.path)
        else:
            print("\n✗ Skill rejected")
            return None

    finally:
        # Cleanup temp directory if not moved
        if temp_dir.exists() and not keep_repo:
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert GitHub repository to Claude skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/pipeline.py https://github.com/user/repo
  python src/pipeline.py https://github.com/user/repo --output ./skills
  python src/pipeline.py https://github.com/user/repo --auto --level 3
        """
    )
    parser.add_argument("github_url", help="GitHub repository URL")
    default_out_dir = str(Path(__file__).resolve().parent.parent.parent)
    parser.add_argument("--output", default=default_out_dir, help="Output directory for generated skills")
    parser.add_argument("--auto", action="store_true", help="Auto-approve without interactive review")
    parser.add_argument("--level", type=int, default=4, choices=[1, 2, 3, 4], help="Validation level")
    parser.add_argument("--keep-repo", action="store_true", default=False, help="Keep cloned repo in skill directory")
    parser.add_argument("--no-keep-repo", action="store_false", dest="keep_repo", help="Remove cloned repo after generation")

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_full_pipeline(
        args.github_url,
        output_dir,
        args.auto,
        args.level,
        args.keep_repo
    )

    if result:
        print("\n" + "=" * 50)
        print("NEXT STEPS")
        print("=" * 50)
        print(f"1. Review: {result}/SKILL.md")
        print(f"2. Test: Run capabilities locally")
        print(f"3. Install: Copy to .claude/skills/ or VenusFactory/skills/")
        sys.exit(0)
    else:
        print("\nPipeline failed or rejected")
        sys.exit(1)


if __name__ == "__main__":
    main()