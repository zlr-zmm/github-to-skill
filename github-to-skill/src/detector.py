"""
Project Detector - Auto-detect GitHub project type, dependencies, and entry points.

Usage:
    python src/detector.py <repo_path> [--output json|yaml]
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class ProjectType(Enum):
    PYTHON_CLI = "python-cli"
    PYTHON_LIB = "python-lib"
    NODE_CLI = "node-cli"
    NODE_LIB = "node-lib"
    RUST_CLI = "rust-cli"
    RUST_LIB = "rust-lib"
    GO_CLI = "go-cli"
    GO_LIB = "go-lib"
    CPP_CLI = "cpp-cli"
    CPP_LIB = "cpp-lib"
    REST_API = "rest-api"
    UNKNOWN = "unknown"


class BuildSystem(Enum):
    SETUPTOOLS = "setuptools"
    POETRY = "poetry"
    FLIT = "flit"
    HATCH = "hatch"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    CARGO = "cargo"
    GO_MODULES = "go-modules"
    CMAKE = "cmake"
    MAKE = "make"
    MESON = "meson"
    UNKNOWN = "unknown"


@dataclass
class EntryPoint:
    name: str
    path: str
    type: str  # "cli", "module", "function"
    description: Optional[str] = None


@dataclass
class DependencyInfo:
    file: str
    format: str  # "pip", "npm", "cargo", etc.
    count: int
    main_deps: list = field(default_factory=list)


@dataclass
class ProjectProfile:
    """Complete project profile for skill generation."""
    path: str
    name: str
    project_type: ProjectType
    build_system: BuildSystem
    language: str
    entry_points: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    has_tests: bool = False
    has_examples: bool = False
    has_docs: bool = False
    readme_path: Optional[str] = None
    wiki_available: bool = False
    license: Optional[str] = None
    confidence: float = 0.0  # Detection confidence score


# File patterns for project type detection
PROJECT_SIGNATURES = {
    ProjectType.PYTHON_CLI: [
        ("pyproject.toml", r"(project\.scripts|project\.entry-points)"),
        ("setup.py", r"entry_points"),
        ("__main__.py", None),
        ("cli.py", None),
        ("main.py", None),
    ],
    ProjectType.PYTHON_LIB: [
        ("pyproject.toml", r"\[project\]"),
        ("setup.py", None),
        ("setup.cfg", None),
        ("__init__.py", None),
    ],
    ProjectType.NODE_CLI: [
        ("package.json", r"bin"),
    ],
    ProjectType.NODE_LIB: [
        ("package.json", r"main|exports"),
    ],
    ProjectType.RUST_CLI: [
        ("Cargo.toml", None),
    ],
    ProjectType.RUST_LIB: [
        ("Cargo.toml", r"\[lib\]"),
    ],
    ProjectType.GO_CLI: [
        ("main.go", None),
        ("go.mod", None),
    ],
    ProjectType.GO_LIB: [
        ("go.mod", None),
    ],
    ProjectType.CPP_CLI: [
        ("CMakeLists.txt", r"add_executable"),
        ("Makefile", None),
    ],
    ProjectType.CPP_LIB: [
        ("CMakeLists.txt", r"add_library"),
    ],
    ProjectType.REST_API: [
        ("app.py", r"flask|fastapi|express"),
        ("main.py", r"flask|fastapi"),
        ("routes/", None),
        ("api/", None),
    ],
}


def detect_project_type(repo_path: Path) -> tuple[ProjectType, float]:
    """Detect project type with confidence score."""
    scores = {}

    for ptype, signatures in PROJECT_SIGNATURES.items():
        score = 0.0
        for filename, pattern in signatures:
            file_path = repo_path / filename
            if file_path.exists():
                if pattern:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 2.0
                    else:
                        score += 0.5
                else:
                    score += 1.0
        if score > 0:
            scores[ptype] = score

    if not scores:
        return ProjectType.UNKNOWN, 0.0

    best_type = max(scores, key=scores.get)
    # Normalize confidence to 0-1 range
    max_possible = 3.0  # Approximate max score per type
    confidence = min(scores[best_type] / max_possible, 1.0)
    return best_type, confidence


def detect_build_system(repo_path: Path, project_type: ProjectType) -> BuildSystem:
    """Detect build system based on project type."""

    if project_type in (ProjectType.PYTHON_CLI, ProjectType.PYTHON_LIB):
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            if "poetry" in content.lower():
                return BuildSystem.POETRY
            if "flit" in content.lower():
                return BuildSystem.FLIT
            if "hatch" in content.lower():
                return BuildSystem.HATCH
        if (repo_path / "setup.py").exists():
            return BuildSystem.SETUPTOOLS
        if (repo_path / "setup.cfg").exists():
            return BuildSystem.SETUPTOOLS

    elif project_type in (ProjectType.NODE_CLI, ProjectType.NODE_LIB):
        if (repo_path / "yarn.lock").exists():
            return BuildSystem.YARN
        if (repo_path / "pnpm-lock.yaml").exists():
            return BuildSystem.PNPM
        if (repo_path / "package-lock.json").exists():
            return BuildSystem.NPM

    elif project_type in (ProjectType.RUST_CLI, ProjectType.RUST_LIB):
        return BuildSystem.CARGO

    elif project_type in (ProjectType.GO_CLI, ProjectType.GO_LIB):
        return BuildSystem.GO_MODULES

    elif project_type in (ProjectType.CPP_CLI, ProjectType.CPP_LIB):
        if (repo_path / "CMakeLists.txt").exists():
            return BuildSystem.CMAKE
        if (repo_path / "Makefile").exists():
            return BuildSystem.MAKE

    return BuildSystem.UNKNOWN


def extract_python_entry_points(repo_path: Path) -> list[EntryPoint]:
    """Extract entry points from Python project."""
    entries = []

    # Check pyproject.toml
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        # Parse [project.scripts] section
        scripts_match = re.search(
            r"\[project\.scripts\]\s*\n((?:\s*\w+\s*=\s*[^\n]+\n?)+)",
            content, re.IGNORECASE
        )
        if scripts_match:
            for line in scripts_match.group(1).strip().split("\n"):
                if "=" in line:
                    name, path = line.split("=")
                    entries.append(EntryPoint(
                        name=name.strip(),
                        path=path.strip().replace(":", "."),
                        type="cli"
                    ))

    # Check setup.py
    setup_py = repo_path / "setup.py"
    if setup_py.exists():
        content = setup_py.read_text(encoding="utf-8", errors="ignore")
        entry_match = re.search(
            r"entry_points\s*=\s*\{[^}]*\"console_scripts\"[^}]*\}",
            content, re.IGNORECASE
        )
        if entry_match:
            # Extract script names
            for match in re.finditer(r"['\"](\w+)['\"]\s*=\s*['\"]([^'\"]+)['\"]", entry_match.group(0)):
                entries.append(EntryPoint(
                    name=match.group(1),
                    path=match.group(2).replace(":", "."),
                    type="cli"
                ))

    # Check __main__.py
    for main_file in ["__main__.py", "cli.py", "main.py"]:
        main_path = repo_path / main_file
        if main_path.exists() and not any(e.path == main_file for e in entries):
            entries.append(EntryPoint(
                name=repo_path.name,
                path=main_file,
                type="cli"
            ))

    return entries


def extract_node_entry_points(repo_path: Path) -> list[EntryPoint]:
    """Extract entry points from Node project."""
    entries = []
    package_json = repo_path / "package.json"

    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            # Check bin field
            if "bin" in data:
                bin_field = data["bin"]
                if isinstance(bin_field, str):
                    entries.append(EntryPoint(
                        name=data.get("name", repo_path.name),
                        path=bin_field,
                        type="cli"
                    ))
                elif isinstance(bin_field, dict):
                    for name, path in bin_field.items():
                        entries.append(EntryPoint(
                            name=name,
                            path=path,
                            type="cli"
                        ))
            # Check main field for library
            if "main" in data and not entries:
                entries.append(EntryPoint(
                    name=data.get("name", repo_path.name),
                    path=data["main"],
                    type="module"
                ))
        except json.JSONDecodeError:
            pass

    return entries


def extract_rust_entry_points(repo_path: Path) -> list[EntryPoint]:
    """Extract entry points from Rust project."""
    entries = []
    cargo_toml = repo_path / "Cargo.toml"

    if cargo_toml.exists():
        content = cargo_toml.read_text(encoding="utf-8", errors="ignore")
        # Check for binary targets
        bin_match = re.search(r"\[\[bin\]\]\s*\n(?:name\s*=\s*['\"](\w+)['\"]\s*\n)?", content)
        if bin_match:
            name = bin_match.group(1) if bin_match.group(1) else repo_path.name
            entries.append(EntryPoint(
                name=name,
                path="src/main.rs",
                type="cli"
            ))
        # Default main.rs
        if (repo_path / "src" / "main.rs").exists() and not entries:
            entries.append(EntryPoint(
                name=repo_path.name,
                path="src/main.rs",
                type="cli"
            ))
        # lib.rs for library
        if (repo_path / "src" / "lib.rs").exists():
            entries.append(EntryPoint(
                name=repo_path.name,
                path="src/lib.rs",
                type="module"
            ))

    return entries


def extract_go_entry_points(repo_path: Path) -> list[EntryPoint]:
    """Extract entry points from Go project."""
    entries = []

    # Check for main.go
    if (repo_path / "main.go").exists():
        entries.append(EntryPoint(
            name=repo_path.name,
            path="main.go",
            type="cli"
        ))

    # Check cmd/ directory for multiple binaries
    cmd_dir = repo_path / "cmd"
    if cmd_dir.exists() and cmd_dir.is_dir():
        for subdir in cmd_dir.iterdir():
            if subdir.is_dir() and (subdir / "main.go").exists():
                entries.append(EntryPoint(
                    name=subdir.name,
                    path=f"cmd/{subdir.name}/main.go",
                    type="cli"
                ))

    return entries


def extract_dependencies(repo_path: Path, project_type: ProjectType) -> list[DependencyInfo]:
    """Extract dependency information."""
    deps = []

    if project_type in (ProjectType.PYTHON_CLI, ProjectType.PYTHON_LIB):
        # requirements.txt
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text(encoding="utf-8", errors="ignore")
            lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]
            deps.append(DependencyInfo(
                file="requirements.txt",
                format="pip",
                count=len(lines),
                main_deps=lines[:10]  # Top 10
            ))

        # pyproject.toml dependencies
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            deps_match = re.search(r"dependencies\s*=\s*\[([^\]]+)\]", content)
            if deps_match:
                dep_list = re.findall(r"['\"]([^'\"]+)['\"]", deps_match.group(1))
                deps.append(DependencyInfo(
                    file="pyproject.toml",
                    format="toml",
                    count=len(dep_list),
                    main_deps=dep_list[:10]
                ))

    elif project_type in (ProjectType.NODE_CLI, ProjectType.NODE_LIB):
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding="utf-8"))
                dep_sections = ["dependencies", "devDependencies", "peerDependencies"]
                for section in dep_sections:
                    if section in data:
                        items = list(data[section].keys())
                        deps.append(DependencyInfo(
                            file=f"package.json:{section}",
                            format="npm",
                            count=len(items),
                            main_deps=items[:10]
                        ))
            except json.JSONDecodeError:
                pass

    elif project_type in (ProjectType.RUST_CLI, ProjectType.RUST_LIB):
        cargo_toml = repo_path / "Cargo.toml"
        if cargo_toml.exists():
            content = cargo_toml.read_text(encoding="utf-8", errors="ignore")
            deps_match = re.search(r"\[dependencies\]\s*\n((?:\w+[^\n]+\n?)+)", content)
            if deps_match:
                lines = deps_match.group(1).strip().split("\n")
                dep_names = [l.split("=")[0].strip() if "=" in l else l.strip() for l in lines if l.strip()]
                deps.append(DependencyInfo(
                    file="Cargo.toml",
                    format="cargo",
                    count=len(dep_names),
                    main_deps=dep_names[:10]
                ))

    return deps


def check_special_features(repo_path: Path) -> dict:
    """Check for tests, examples, docs, wiki."""
    features = {
        "has_tests": False,
        "has_examples": False,
        "has_docs": False,
        "wiki_available": False,
        "readme_path": None,
        "license": None,
    }

    # Tests
    test_patterns = ["tests/", "test/", "pytest/", "__tests/", "spec/", "*_test.py", "*_test.go"]
    for pattern in test_patterns:
        if pattern.endswith("/"):
            if (repo_path / pattern.rstrip("/")).exists():
                features["has_tests"] = True
                break
        else:
            if list(repo_path.glob(pattern)):
                features["has_tests"] = True
                break

    # Examples
    example_dirs = ["examples/", "example/", "demo/", "samples/"]
    for dir_name in example_dirs:
        if (repo_path / dir_name.rstrip("/")).exists():
            features["has_examples"] = True
            break

    # Docs
    doc_dirs = ["docs/", "documentation/", "doc/"]
    for dir_name in doc_dirs:
        if (repo_path / dir_name.rstrip("/")).exists():
            features["has_docs"] = True
            break

    # README
    readme_names = ["README.md", "README.rst", "README.txt", "readme.md"]
    for name in readme_names:
        readme_path = repo_path / name
        if readme_path.exists():
            features["readme_path"] = name
            break

    # License
    license_names = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
    for name in license_names:
        license_path = repo_path / name
        if license_path.exists():
            content = license_path.read_text(encoding="utf-8", errors="ignore")
            if "MIT" in content:
                features["license"] = "MIT"
            elif "Apache" in content:
                features["license"] = "Apache-2.0"
            elif "GPL" in content:
                features["license"] = "GPL"
            elif "BSD" in content:
                features["license"] = "BSD"
            break

    return features


def detect_language(project_type: ProjectType) -> str:
    """Get primary language from project type."""
    language_map = {
        ProjectType.PYTHON_CLI: "Python",
        ProjectType.PYTHON_LIB: "Python",
        ProjectType.NODE_CLI: "JavaScript/TypeScript",
        ProjectType.NODE_LIB: "JavaScript/TypeScript",
        ProjectType.RUST_CLI: "Rust",
        ProjectType.RUST_LIB: "Rust",
        ProjectType.GO_CLI: "Go",
        ProjectType.GO_LIB: "Go",
        ProjectType.CPP_CLI: "C/C++",
        ProjectType.CPP_LIB: "C/C++",
        ProjectType.REST_API: "Mixed",
        ProjectType.UNKNOWN: "Unknown",
    }
    return language_map.get(project_type, "Unknown")


def profile_project(repo_path: str) -> ProjectProfile:
    """Complete project profiling."""
    path = Path(repo_path)

    if not path.exists():
        raise FileNotFoundError(f"Repository path not found: {repo_path}")

    # Detect type
    project_type, confidence = detect_project_type(path)

    # Detect build system
    build_system = detect_build_system(path, project_type)

    # Extract entry points based on type
    entry_extractors = {
        ProjectType.PYTHON_CLI: extract_python_entry_points,
        ProjectType.PYTHON_LIB: extract_python_entry_points,
        ProjectType.NODE_CLI: extract_node_entry_points,
        ProjectType.NODE_LIB: extract_node_entry_points,
        ProjectType.RUST_CLI: extract_rust_entry_points,
        ProjectType.RUST_LIB: extract_rust_entry_points,
        ProjectType.GO_CLI: extract_go_entry_points,
        ProjectType.GO_LIB: extract_go_entry_points,
    }

    entries = entry_extractors.get(project_type, lambda x: [])(path)

    # Extract dependencies
    dependencies = extract_dependencies(path, project_type)

    # Check special features
    features = check_special_features(path)

    return ProjectProfile(
        path=repo_path,
        name=path.name,
        project_type=project_type,
        build_system=build_system,
        language=detect_language(project_type),
        entry_points=entries,
        dependencies=dependencies,
        has_tests=features["has_tests"],
        has_examples=features["has_examples"],
        has_docs=features["has_docs"],
        readme_path=features["readme_path"],
        wiki_available=features["wiki_available"],
        license=features["license"],
        confidence=confidence,
    )


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect GitHub project profile")
    parser.add_argument("repo_path", help="Local repository path")
    parser.add_argument("--output", choices=["json", "yaml"], default="json", help="Output format")

    args = parser.parse_args()

    try:
        profile = profile_project(args.repo_path)

        # Convert to dict
        data = asdict(profile)
        data["project_type"] = profile.project_type.value
        data["build_system"] = profile.build_system.value

        if args.output == "json":
            print(json.dumps(data, indent=2))
        else:
            # Simple YAML output
            print(f"path: {data['path']}")
            print(f"name: {data['name']}")
            print(f"project_type: {data['project_type']}")
            print(f"build_system: {data['build_system']}")
            print(f"language: {data['language']}")
            print(f"confidence: {data['confidence']}")
            print(f"entry_points:")
            for ep in data["entry_points"]:
                print(f"  - name: {ep['name']}, path: {ep['path']}, type: {ep['type']}")
            print(f"dependencies:")
            for dep in data["dependencies"]:
                print(f"  - file: {dep['file']}, count: {dep['count']}")
            print(f"has_tests: {data['has_tests']}")
            print(f"has_examples: {data['has_examples']}")
            print(f"has_docs: {data['has_docs']}")
            print(f"readme_path: {data['readme_path']}")
            print(f"license: {data['license']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()