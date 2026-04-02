# Phase 1: Harvest

## Goal

Create a runnable baseline, collect evidence, and complete code checks.

## Step 1: Clone, Install, Smoke Test

```powershell
git clone <github_url> <local_repo_dir>
cd <local_repo_dir>
git rev-parse HEAD
```

Python example:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
python -c "import <package_name>"
```

CLI smoke test:

```powershell
<cli-name> --help
```

If smoke test fails, mark `blocked` and stop before Phase 2.

## Step 2: Evidence Harvest (Wiki > README)

Allowed evidence:

1. Wiki (primary)
2. README (secondary)

Do not use papers as capability evidence.

## Step 3: Mandatory Code Check

Check all three:

1. Entrypoints: `pyproject.toml`, `setup.py`, `package.json`
2. Parameters: `argparse`, `click`, `typer`, `yargs`
3. Output behavior: output files or API responses

Only checked capabilities can be included in final skill output.

## Exit Criteria

At least one capability has:

- accepted evidence
- passed code check
