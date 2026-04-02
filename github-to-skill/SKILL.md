---
name: github-to-skill
description: Convert a GitHub repository into a runnable Claude skill using intelligent 5-step pipeline with automatic project detection, evidence extraction, and adaptive template generation.
license: MIT
---

# github-to-skills

Automated factory for converting GitHub repositories into specialized AI skills.

## Features
- Fetches repository metadata (README, latest commit hash) 
- Creates standardized skill directory structure 
- Generates SKILL.md with extended frontmatter for lifecycle management 
- Creates wrapper scripts for tool invocation 

## Usage
`/github-to-skills <github_url>`
Or: "Package this repo into a skill: <github_url>"

## Example
`/github-to-skills https://github.com/zlr-zmm/github-to-skill`

## Pipeline Overview

This skill transforms GitHub repositories into structured Claude Code skills through an intelligent 5-step pipeline:

```
GitHub URL → Detect → Extract → Generate → Validate → Review → Skill
```

## 5-Step Pipeline

### Step 1: Detect (Project Profiling)

**Goal**: Automatically identify project characteristics.

**Detection Targets**:
- Project type: Python CLI / Python Lib / Node CLI / Rust CLI / Go CLI / REST API
- Build system: setuptools / poetry / npm / cargo / cmake
- Entry points: CLI commands, module imports, API endpoints
- Dependencies: requirements.txt, package.json, Cargo.toml
- Special features: tests, examples, docs, wiki

**Tool**: `src/detector.py`

**Output**: `ProjectProfile` JSON with confidence score

**Example**:
```bash
python src/detector.py ./cloned-repo --output json
```

### Step 2: Extract (Evidence Collection)

**Goal**: Gather functional evidence from multiple sources.

**Evidence Priority**:
```
Project Docs > Wiki > README > Examples > Tests > Source Comments
```

**Extraction Rules**:
1. Do NOT use academic papers as capability evidence
2. Code examples from `examples/` directory are primary evidence
3. Test cases provide behavioral validation evidence
4. Source comments clarify parameter constraints

**Output**: `references/source-notes.md`

### Step 3: Generate (Adaptive Templating)

**Goal**: Create skill artifacts using type-appropriate templates.

**Template Selection**:
| Project Type | Template | Wrapper Style |
|--------------|----------|---------------|
| Python CLI | `python-cli.md` | subprocess |
| Python Lib | `python-lib.md` | import |
| Node CLI | `node-cli.md` | subprocess/npx |
| Rust CLI | `rust-cli.md` | binary call |
| REST API | `rest-api.md` | HTTP requests |

**Output Files**:
- `SKILL.md` - Skill definition with capabilities
- `scripts/wrapper.py` - Execution wrapper (if CLI)
- `references/workflow.md` - Capability workflow map

### Step 4: Validate (Progressive Verification)

**Goal**: Prove generated skill is executable.

**Validation Levels**:
| Level | Check | Pass Criteria |
|-------|-------|---------------|
| 1 | Structure | All required files exist |
| 2 | Syntax | Wrapper script syntax valid |
| 3 | Dependencies | Requirements installable |
| 4 | Function | At least one capability executes |

**Failure Handling**:
- `blocked`: Setup failed → provide unblock commands
- `partial`: Some capabilities verified → list verified/unverified
- `ready`: All gates passed → usable

**Output**: Validation report summary

### Step 5: Review (User Confirmation)

**Goal**: Interactive approval of generated skill.

**Decision Points**:
1. **Function Filter**: "Found 15 capabilities, select to include"
2. **Entry Confirmation**: "Detected 3 entry points, choose primary"
3. **Validation Level**: "Quick / Basic / Full validation?"

**Final Output**: User-approved `SKILL.md`

## Status Model

| Status | Meaning | Required Block |
|--------|---------|----------------|
| `ready` | All gates passed | None |
| `partial` | Some gates passed | WARNING block required |
| `blocked` | Setup failed | Unblock commands required |

**WARNING Block Format** (mandatory for `partial`):
```markdown
> WARNING: Partial validation. The following capabilities are not locally verified:
> - [Capability]: [Reason]
> Unblock step: [Action]
```

## Project Type Detection

### Detection Rules

1. **Python CLI**: Has `[project.scripts]` in pyproject.toml OR `entry_points` in setup.py OR `__main__.py`
2. **Python Lib**: Has `[project]` without scripts OR `__init__.py` in package
3. **Node CLI**: Has `bin` field in package.json
4. **Rust CLI**: Has `src/main.rs` OR `[[bin]]` in Cargo.toml
5. **Go CLI**: Has `main.go` OR `cmd/*/main.go`
6. **REST API**: Has `app.py` with flask/fastapi OR `routes/` OR `api/` directory

### Confidence Scoring

- Each signature match adds points
- Score normalized to 0.0-1.0 range
- `confidence < 0.5` → manual review required

## Scope Constraints

**This skill processes only the user-specified target repository.**

Hard constraints:
1. Do not modify unrelated skills
2. Do not modify files unrelated to target repository conversion
3. Do not use papers as capability evidence

## Installation Commands

### Python Projects

```powershell
# Clone
git clone <github_url> <local_repo_dir>
cd <local_repo_dir>

# Virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip

# Install dependencies
pip install -r requirements.txt
# or: pip install .
```

### Node Projects

```powershell
git clone <github_url> <local_repo_dir>
cd <local_repo_dir>
npm install
```

### Rust Projects

```powershell
git clone <github_url> <local_repo_dir>
cd <local_repo_dir>
cargo build --release
```

## Generated Skill Structure

```
generated-skill/
├── SKILL.md              # Skill definition (from template)
├── scripts/
│   └── wrapper.py        # Execution wrapper
├── references/
│   ├── source-notes.md   # Evidence sources
│   └── workflow.md       # Capability map
└── assets/               # Optional: diagrams, examples
```

## Pipeline Execution

**Interactive Mode** (recommended):
```
User provides GitHub URL
→ Step 1: Detect (auto)
→ Step 2: Extract (auto + LLM assist)
→ Step 3: Generate (auto, template-based)
→ Step 4: Validate (auto, progressive)
→ Step 5: Review (interactive)
→ Final: Approved SKILL.md
```

**Automated Mode** (for trusted repos):
```
python src/pipeline.py <github_url> --output <skill_dir> --auto
```

**Manual Step Execution**:
```bash
# Step 1: Profile
python src/detector.py ./repo --output json > profile.json

# Step 2: Extract (manual or LLM-assisted)
# Read README, Wiki, examples

# Step 3: Generate
python src/generator.py profile.json --template python-cli

# Step 4: Validate
python src/validator.py ./generated-skill

# Step 5: Review (user edits SKILL.md)
```

## Best Practices

1. **Isolation**: Generated skills should install own dependencies
2. **Progressive Disclosure**: Include only necessary wrapper, reference repo for details
3. **Idempotency**: `github_hash` enables version tracking and safe updates
4. **Evidence Traceability**: Every capability links to source evidence
5. **Validation Transparency**: Test report shows exactly what was verified

## References

Load on demand:
- `references/phase1-harvest.md` - Detailed detection guide
- `references/phase2-generate.md` - Template application guide
- `references/phase3-validate.md` - Validation checklist
- `templates/python-cli.md` - Python CLI template
- `templates/python-lib.md` - Python library template
- `templates/node-cli.md` - Node CLI template
- `templates/rust-cli.md` - Rust CLI template
- `templates/rest-api.md` - REST API template

## Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `src/detector.py` | Project profiling | `python src/detector.py <repo_path>` |
| `src/generator.py` | Template rendering | `python src/generator.py <profile.json>` |
| `src/validator.py` | Skill validation | `python src/validator.py <skill_dir>` |
| `src/pipeline.py` | Full pipeline | `python src/pipeline.py <github_url>` |